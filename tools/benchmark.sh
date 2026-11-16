#!/usr/bin/env bash
# OS-vs-OS benchmark for Intel Macs: runs unchanged on Linux and macOS (bash 3.2, stock perl).
# Meant for the SAME Mac booted into each OS, so the chip cancels out (docs/benchmark.md).
# Measures the machine AS IS: never touches turbo, governors, power profiles or fans.
#
#   user-space tests (the CPU baseline): sha256 1-core / all threads, perl int loop, gzip
#   kernel tests: syscall rate, stat, pipe round trips, fork, fork+exec, file create/unlink,
#                 page faults on fresh memory, dd zero-fill
#   kernel results are also reported per unit of single-core CPU speed ("normalized"), which
#   cancels clock/turbo differences, so the kernel's efficiency per CPU cycle is compared.
#
#   bash benchmark.sh --runs 10 --json --out DIR     # medians -> DIR/linux.json or DIR/macos.json
#   bash benchmark.sh --quick                        # short check run
#   compare: tools/benchmark-compare.sh DIR/linux.json DIR/macos.json
# Higher is better everywhere. No AES-NI path (sha256 on integer units; no SHA-NI on this CPU).
set -u
LC_ALL=C; export LC_ALL
QUICK=0; RUNS=1; JSON=0; OUTDIR=.
while [ $# -gt 0 ]; do
  case "$1" in
    --quick) QUICK=1 ;;
    --runs) RUNS=$2; shift ;;
    --json) JSON=1 ;;
    --out) OUTDIR=$2; shift ;;
    *) echo "usage: benchmark.sh [--runs N] [--json] [--out DIR] [--quick]" >&2; exit 2 ;;
  esac
  shift
done
mkdir -p "$OUTDIR"
OS=$(uname -s)
STAMP=$(date +%Y%m%d-%H%M%S)
TXT="$OUTDIR/benchmark-$(echo "$OS" | tr 'A-Z' 'a-z')-${STAMP}.txt"
exec > >(tee "$TXT") 2>&1

if [ "$OS" = Darwin ]; then
  NAME=macos
  CPU=$(sysctl -n machdep.cpu.brand_string); NCPU=$(sysctl -n hw.logicalcpu); PCPU=$(sysctl -n hw.physicalcpu)
  MEM=$(( $(sysctl -n hw.memsize) / 1073741824 ))
  MODEL=$(sysctl -n hw.model)
  POWER=$(pmset -g batt 2>/dev/null | sed -n 's/.*Now drawing from //p' | tr -d "'")
  TURBO="n/a"; GOV="n/a"; EPP="n/a"
  PROFILE="lowpowermode=$(pmset -g 2>/dev/null | awk '/lowpowermode/{print $2}')"
  OSV="macOS $(sw_vers -productVersion) (Darwin $(uname -r))"
else
  NAME=linux
  CPU=$(sed -n 's/^model name\s*:\s*//p' /proc/cpuinfo | head -1); NCPU=$(nproc)
  PCPU=$(lscpu -p=core 2>/dev/null | grep -v '^#' | sort -u | wc -l | tr -d ' ')
  MEM=$(( $(awk '/MemTotal/{print $2}' /proc/meminfo) / 1048576 ))
  MODEL=$(cat /sys/class/dmi/id/product_name 2>/dev/null || echo unknown)
  POWER=$(cat /sys/class/power_supply/*/online 2>/dev/null | head -1 | sed 's/1/AC/; s/0/battery/')
  TURBO=$( [ "$(cat /sys/devices/system/cpu/intel_pstate/no_turbo 2>/dev/null)" = 1 ] && echo off || echo on)
  GOV=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null)
  EPP=$(cat /sys/devices/system/cpu/cpu0/cpufreq/energy_performance_preference 2>/dev/null)
  PROFILE=$(powerprofilesctl get 2>/dev/null || echo n/a)
  OSV="$(. /etc/os-release 2>/dev/null; echo "$PRETTY_NAME") (Linux $(uname -r))"
fi
echo "== benchmark $STAMP ($RUNS run(s)$([ $QUICK = 1 ] && echo ', quick'))"
echo "os:     $OSV"
echo "mac:    $MODEL"
echo "cpu:    $CPU ($PCPU cores / $NCPU threads), ${MEM} GiB RAM"
echo "power:  ${POWER:-unknown}  turbo=$TURBO governor=$GOV epp=$EPP profile=$PROFILE"
echo "tools:  $(openssl version)  perl $(perl -e 'print $^V')"
echo

# sizes: full / quick
q() { [ $QUICK = 1 ] && echo "$2" || echo "$1"; }
SECS=$(q 3 1); PERL_N=$(q 20000000 3000000); GB=$(q 32 4); MBYTES=$(q 512 64)
SYS_N=$(q 4000000 1000000); STAT_N=$(q 1000000 200000); PIPE_N=$(q 100000 20000)
FORK_N=$(q 3000 500); SPAWN_N=$(q 2000 300); FILES_N=$(q 5000 1000); FAULT_MB=$(q 2048 512)
BS=$([ "$OS" = Darwin ] && echo 1m || echo 1M)

now() { perl -MTime::HiRes=time -e 'printf "%.6f\n", time'; }
speed() {  # last column (16384-byte blocks, kB/s) of the sha256 line
  openssl speed $1 2>/dev/null | awk '/^sha256/{v=$NF} END{sub(/k$/,"",v); print v}'
}
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
DATA="$WORK/data"
perl -e 'srand(42); my @w=qw(kernel memory cache thread intel apple linux macbook audio speaker battery);
  while(1){ print join(" ", map { $w[rand @w] } 1..12), "\n" }' 2>/dev/null | head -c $((MBYTES*1048576)) > "$DATA"

# kernel micro-tests, timed inside perl (no interpreter start-up in the measurement)
ktest() {
  BDIR="$WORK" perl -MTime::HiRes=time -MPOSIX -e '
    my ($k, $n) = @ARGV; my $t0 = time; my $b;
    if ($k eq "stat") { for (1..$n) { my @s = stat("/") } }
    elsif ($k eq "pipe") {
      pipe(my $ar, my $aw); pipe(my $br, my $bw); my $p = fork;
      if (!$p) { close $aw; close $br; while (sysread($ar, $b, 1)) { syswrite($bw, $b, 1) } POSIX::_exit(0) }
      close $ar; close $bw; for (1..$n) { syswrite($aw, "x", 1); sysread($br, $b, 1) } close $aw; waitpid($p, 0) }
    elsif ($k eq "fork") { for (1..$n) { my $p = fork; POSIX::_exit(0) unless $p; waitpid($p, 0) } }
    elsif ($k eq "spawn") { for (1..$n) { my $p = fork; if (!$p) { exec "/usr/bin/true"; POSIX::_exit(127) } waitpid($p, 0) } }
    elsif ($k eq "files") { my $d = $ENV{BDIR};
      for (1..$n) { open(my $f, ">", "$d/f$_") or die "$!"; close $f } unlink "$d/f$_" for 1..$n }
    elsif ($k eq "fault") { my $x = "\1" x ($n * 1048576) }
    my $dt = time - $t0; printf "%.1f", $k eq "fault" ? $n / 1024 / $dt : $k =~ /^(fork|spawn)$/ ? $n / $dt : $n / $dt / 1000;' "$1" "$2"
}

# metric registry: key|unit|kind|label  (kind: cpu = user space baseline, kernel)
METRICS="sha1|MB/s|cpu|sha256 single-core
shaN|MB/s|cpu|sha256 all $NCPU threads
perl|M iter/s|cpu|perl integer loop
gzip|MB/s|cpu|gzip -6 single-core
syscall|k calls/s|kernel|tiny syscalls (dd 1-byte read+write)
stat|k calls/s|kernel|stat(/) path lookup
pipe|k round trips/s|kernel|pipe ping-pong (context switches)
fork|forks/s|kernel|fork + exit + wait
spawn|spawns/s|kernel|fork + exec /usr/bin/true
files|k files/s|kernel|file create + unlink (also the filesystem)
fault|GiB/s|kernel|fresh memory (page faults + fill)
zero|GiB/s|kernel|dd /dev/zero -> /dev/null 1 MiB"
KEYS=$(echo "$METRICS" | cut -d'|' -f1 | tr '\n' ' ')
for k in $KEYS; do eval "V_$k=''"; done
add() { eval "V_$1=\"\$V_$1 $2\""; }

run=1
while [ $run -le "$RUNS" ]; do
  s=$(speed "-seconds $SECS sha256"); [ -z "$s" ] && s=$(speed "sha256")
  m=$(speed "-multi $NCPU -seconds $SECS sha256"); [ -z "$m" ] && m=$(speed "-multi $NCPU sha256")
  add sha1 "$(perl -e "printf '%.0f', ${s:-0}/1000")"; add shaN "$(perl -e "printf '%.0f', ${m:-0}/1000")"
  t0=$(now); perl -e "my \$s=0; for my \$i (1..$PERL_N) { \$s += (\$i % 7) * (\$i & 15) } print '' if \$s<0"; t1=$(now)
  add perl "$(perl -e "printf '%.2f', $PERL_N/($t1-$t0)/1e6")"
  t0=$(now); gzip -6 -c "$DATA" > /dev/null; t1=$(now)
  add gzip "$(perl -e "printf '%.1f', $MBYTES/($t1-$t0)")"
  t0=$(now); dd if=/dev/zero of=/dev/null bs=1 count=$SYS_N 2>/dev/null; t1=$(now)
  add syscall "$(perl -e "printf '%.1f', 2*$SYS_N/($t1-$t0)/1000")"
  add stat "$(ktest stat $STAT_N)"; add pipe "$(ktest pipe $PIPE_N)"
  add fork "$(ktest fork $FORK_N)"; add spawn "$(ktest spawn $SPAWN_N)"
  add files "$(ktest files $FILES_N)"; add fault "$(ktest fault $FAULT_MB)"
  t0=$(now); dd if=/dev/zero of=/dev/null bs=$BS count=$((GB*1024)) 2>/dev/null; t1=$(now)
  add zero "$(perl -e "printf '%.2f', $GB/($t1-$t0)")"
  line="run $run/$RUNS:"; for k in $KEYS; do eval "v=\${V_$k##* }"; line="$line $k=$v"; done; echo "$line"
  run=$((run + 1))
done

median() { perl -e '@v=sort { $a <=> $b } @ARGV; $n=@v; printf "%s", $n%2 ? $v[$n/2] : ($v[$n/2-1]+$v[$n/2])/2' $1; }
eval "PERL_MED=\$(median \"\$V_perl\")"
echo
echo "median over $RUNS run(s); 'per CPU' = kernel result / single-core perl speed"
echo "$METRICS" | while IFS='|' read -r k unit kind label; do
  eval "vals=\$V_$k"; med=$(median "$vals")
  norm=""; [ "$kind" = kernel ] && norm=$(perl -e "printf 'per CPU %.3f', $med/$PERL_MED")
  printf '  %-6s %-44s %10s %-15s %s\n' "$kind" "$label" "$med" "$unit" "$norm"
done

if [ $JSON = 1 ]; then
  J="$OUTDIR/$NAME.json"
  for k in $KEYS; do eval "export B_V_$k=\"\$V_$k\""; done
  B_METRICS="$METRICS" B_OS="$OSV" B_MODEL="$MODEL" B_CPU="$CPU" B_PCPU="$PCPU" B_NCPU="$NCPU" B_MEM="$MEM" \
  B_POWER="${POWER:-unknown}" B_TURBO="$TURBO" B_GOV="$GOV" B_EPP="$EPP" B_PROFILE="$PROFILE" \
  B_SSL="$(openssl version)" B_PERLV="$(perl -e 'print $^V')" B_RUNS="$RUNS" B_QUICK="$QUICK" B_STAMP="$STAMP" \
  perl -MJSON::PP -e '
    my %o = (os => $ENV{B_OS}, mac_model => $ENV{B_MODEL}, cpu => $ENV{B_CPU}, cores => 0+$ENV{B_PCPU},
             threads => 0+$ENV{B_NCPU}, ram_gib => 0+$ENV{B_MEM}, power => $ENV{B_POWER}, turbo => $ENV{B_TURBO},
             governor => $ENV{B_GOV}, epp => $ENV{B_EPP}, profile => $ENV{B_PROFILE}, openssl => $ENV{B_SSL},
             perl => $ENV{B_PERLV}, runs => 0+$ENV{B_RUNS}, quick => $ENV{B_QUICK} ? JSON::PP::true : JSON::PP::false,
             date => $ENV{B_STAMP},
             note => "higher is better; medians; normalized = kernel median / single-core perl median");
    my %med;
    for my $line (split /\n/, $ENV{B_METRICS}) {
      my ($k, $unit, $kind, $label) = split /\|/, $line;
      my @r = split " ", $ENV{"B_V_$k"}; my @v = sort { $a <=> $b } @r; my $n = @v;
      $med{$k} = $n % 2 ? $v[$n/2] : ($v[$n/2-1] + $v[$n/2]) / 2;
      $o{metrics}{$k} = { median => 0+$med{$k}, min => 0+$v[0], max => 0+$v[-1], unit => $unit, kind => $kind,
                          label => $label, runs => [map { 0+$_ } @r] };
    }
    for my $k (keys %{$o{metrics}}) {
      $o{metrics}{$k}{normalized} = 0+sprintf("%.4f", $med{$k} / $med{perl}) if $o{metrics}{$k}{kind} eq "kernel";
    }
    print JSON::PP->new->canonical->pretty->encode(\%o);' > "$J"
  echo; echo "== medians saved to $J"
fi
echo "== log saved to $TXT"
