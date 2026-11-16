#!/usr/bin/env bash
# Compare two benchmark.sh JSON files (e.g. linux.json vs macos.json).
#   bash benchmark-compare.sh benchmarks/linux.json benchmarks/macos.json
# Refuses to compare different CPUs (that would be chip vs chip); --force shows only the
# normalized kernel numbers, which are the least chip-dependent, with a warning.
set -u
FORCE=0; [ "${1:-}" = "--force" ] && { FORCE=1; shift; }
[ $# -eq 2 ] || { echo "usage: benchmark-compare.sh [--force] a.json b.json" >&2; exit 2; }
FORCE=$FORCE perl -MJSON::PP -e '
  sub load { local $/; open my $f, "<", $_[0] or die "$_[0]: $!\n"; decode_json(<$f>) }
  my ($a, $b) = (load($ARGV[0]), load($ARGV[1]));
  my $same = $a->{cpu} eq $b->{cpu} && $a->{threads} == $b->{threads};
  printf "A: %s\n   %s | %s | power %s turbo %s %s | %d runs\n", $ARGV[0], $a->{os}, $a->{cpu}, $a->{power}, $a->{turbo}, $a->{profile}, $a->{runs};
  printf "B: %s\n   %s | %s | power %s turbo %s %s | %d runs\n\n", $ARGV[1], $b->{os}, $b->{cpu}, $b->{power}, $b->{turbo}, $b->{profile}, $b->{runs};
  if (!$same) {
    print "Different CPUs: a raw comparison would be chip vs chip.\n";
    exit 1 unless $ENV{FORCE};
    print "--force: only normalized kernel results (per unit of single-core CPU speed), still approximate.\n\n";
  }
  print "Different Mac models ($a->{mac_model} vs $b->{mac_model}).\n\n" if $same && $a->{mac_model} ne $b->{mac_model};
  printf "%-6s %-44s %12s %12s %8s %8s\n", "kind", "test", "A", "B", "B/A", "B/A cpu";
  my @order = qw(sha1 shaN perl gzip syscall stat pipe fork spawn files fault zero);
  for my $k (@order) {
    my ($x, $y) = ($a->{metrics}{$k}, $b->{metrics}{$k}); next unless $x && $y;
    next if !$same && $x->{kind} ne "kernel";
    my $raw = $x->{median} ? $y->{median} / $x->{median} : 0;
    my $norm = $x->{kind} eq "kernel" && $x->{normalized} ? sprintf("%8.2f", $y->{normalized} / $x->{normalized}) : "";
    printf "%-6s %-44s %12s %12s %8.2f %8s\n", $x->{kind}, $x->{label}, $x->{median}, $y->{median}, $raw, $norm;
  }
  print "\nB/A > 1: B is faster. \"B/A cpu\" cancels clock/turbo differences (kernel efficiency per CPU cycle).\n";
' "$1" "$2"
