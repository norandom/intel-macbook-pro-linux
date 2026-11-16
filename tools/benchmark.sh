#!/usr/bin/env bash
# Portable CPU / memory benchmark for Intel Macs: runs unchanged on Linux and macOS.
# Measures the machine AS IS: it never touches turbo, governors, power profiles or fans. It
# only uses tools both systems ship (openssl, perl, dd, gzip) and records the power state, so
# runs are comparable (plugged in vs battery, turbo on/off, power profile).
#
#   bash benchmark.sh            # ~2-3 minutes, result file in the current directory
#   bash benchmark.sh --quick    # ~30 s smoke run
#
# Higher is better everywhere. Run twice and compare the second run (the first warms caches).
set -u
LC_ALL=C; export LC_ALL
QUICK=0; [ "${1:-}" = "--quick" ] && QUICK=1
SECS=$([ $QUICK = 1 ] && echo 1 || echo 3)
OS=$(uname -s)
HOST=$(hostname -s 2>/dev/null || hostname)
STAMP=$(date +%Y%m%d-%H%M%S)
OUT="benchmark-${HOST}-${OS}-${STAMP}.txt"
exec > >(tee "$OUT") 2>&1

now() { perl -MTime::HiRes=time -e 'printf "%.6f\n", time'; }
elapsed() { perl -e "printf '%.3f', $2 - $1"; }

if [ "$OS" = Darwin ]; then
  CPU=$(sysctl -n machdep.cpu.brand_string); NCPU=$(sysctl -n hw.logicalcpu); PCPU=$(sysctl -n hw.physicalcpu)
  MEM=$(( $(sysctl -n hw.memsize) / 1073741824 ))
  POWER=$(pmset -g batt 2>/dev/null | sed -n 's/.*Now drawing from //p' | tr -d "'")
  EXTRA="lowpowermode=$(pmset -g 2>/dev/null | awk '/lowpowermode/{print $2}')"
  OSV="macOS $(sw_vers -productVersion)"
else
  CPU=$(sed -n 's/^model name\s*:\s*//p' /proc/cpuinfo | head -1); NCPU=$(nproc); PCPU=$(lscpu -p=core 2>/dev/null | grep -v '^#' | sort -u | wc -l)
  MEM=$(( $(awk '/MemTotal/{print $2}' /proc/meminfo) / 1048576 ))
  POWER=$(cat /sys/class/power_supply/*/online 2>/dev/null | head -1 | sed 's/1/AC/; s/0/battery/')
  EXTRA="turbo=$( [ "$(cat /sys/devices/system/cpu/intel_pstate/no_turbo 2>/dev/null)" = 1 ] && echo off || echo on)"
  EXTRA="$EXTRA governor=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null)"
  EXTRA="$EXTRA epp=$(cat /sys/devices/system/cpu/cpu0/cpufreq/energy_performance_preference 2>/dev/null)"
  EXTRA="$EXTRA profile=$(powerprofilesctl get 2>/dev/null || echo n/a)"
  OSV="$(. /etc/os-release 2>/dev/null; echo "$PRETTY_NAME") kernel $(uname -r)"
fi
echo "== benchmark $STAMP on $HOST"
echo "os:     $OSV"
echo "cpu:    $CPU ($PCPU cores / $NCPU threads), ${MEM} GiB RAM"
echo "power:  ${POWER:-unknown}  $EXTRA"
echo "tools:  $(openssl version)  perl $(perl -e 'print $^V')"
echo

# --- 1. single-core hashing (openssl sha256: plain integer units; Coffee Lake has no SHA-NI) -----
speed() {  # $1 = extra args; prints the last column (16384-byte blocks, in kB/s) of the result line
  openssl speed $1 2>/dev/null | awk '/^sha256/{v=$NF} END{sub(/k$/,"",v); print v}'
}
single_sha=$(speed "-seconds $SECS sha256"); [ -z "$single_sha" ] && single_sha=$(speed "sha256")
mb() { perl -e "printf '%.0f', ${1:-0}/1000"; }
echo "single-core  sha256          $(mb "$single_sha") MB/s"

# --- 2. all cores ------------------------------------------------------------------------------
multi_sha=$(speed "-multi $NCPU -seconds $SECS sha256"); [ -z "$multi_sha" ] && multi_sha=$(speed "-multi $NCPU sha256")
echo "multi-core   sha256 x$NCPU      $(mb "$multi_sha") MB/s   (scaling $(perl -e "printf '%.1f', ${multi_sha:-0}/(${single_sha:-1}||1)")x)"

# --- 3. interpreter / branchy integer code (perl, single thread) --------------------------------
N=$([ $QUICK = 1 ] && echo 3000000 || echo 20000000)
t0=$(now); perl -e "my \$s=0; for my \$i (1..$N) { \$s += (\$i % 7) * (\$i & 15) } print '' if \$s<0"; t1=$(now)
echo "single-core  perl int loop   $(perl -e "printf '%.1f', $N/($t1-$t0)/1e6") M iter/s"

# --- 4. memory bandwidth (dd: zero-fill + copy through the kernel, 1 MiB blocks) ----------------
GB=$([ $QUICK = 1 ] && echo 4 || echo 32)
bs=$([ "$OS" = Darwin ] && echo 1m || echo 1M)
t0=$(now); dd if=/dev/zero of=/dev/null bs=$bs count=$((GB*1024)) 2>/dev/null; t1=$(now)
echo "memory       dd 1 MiB blocks $(perl -e "printf '%.1f', $GB/($t1-$t0)") GiB/s"

# --- 5. compression (gzip -6, single thread, compressible text) --------------------------------
MBYTES=$([ $QUICK = 1 ] && echo 64 || echo 512)
tmp=$(mktemp); perl -e 'srand(42); my @w=qw(kernel memory cache thread intel apple linux macbook audio speaker battery);
  while(1){ print join(" ", map { $w[rand @w] } 1..12), "\n" }' | head -c $((MBYTES*1048576)) > "$tmp"
t0=$(now); gzip -6 -c "$tmp" > /dev/null; t1=$(now); rm -f "$tmp"
echo "single-core  gzip -6         $(perl -e "printf '%.0f', $MBYTES/($t1-$t0)") MB/s"

echo
echo "== saved to $OUT"
