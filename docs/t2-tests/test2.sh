#!/usr/bin/env bash
# Test 2: does writing fan*_target raise the fans? Restores the minimum (SMC automatic) at the end,
# also if interrupted (Ctrl+C).
# Run: bash docs/t2-tests/test2.sh   -> writes docs/t2-tests/test2.log
set -u
H=/sys/devices/pci0000:00/0000:00:1f.0/APP0001:00/macsmc-hwmon/hwmon/hwmon4
LOG="$(cd "$(dirname "$0")" && pwd)/test2.log"
exec > >(tee "$LOG") 2>&1
echo "== test2 fan control  $(date -Is)  kernel $(uname -r)"
min1=$(cat $H/fan1_min); min2=$(cat $H/fan2_min)
show() { echo "  fan1 $(cat $H/fan1_input) rpm (target $(cat $H/fan1_target))  fan2 $(cat $H/fan2_input) rpm (target $(cat $H/fan2_target))  cpu $(awk '{printf "%.0f", $1/1000}' $(grep -l 'TCMX' $H/temp*_label 2>/dev/null | head -1 | sed 's/_label/_input/') 2>/dev/null) C"; }
restore() { echo "restore minimum targets ($min1 / $min2):"; echo "$min1" | sudo tee $H/fan1_target >/dev/null; echo "$min2" | sudo tee $H/fan2_target >/dev/null; sleep 8; show; }
trap restore EXIT
echo "labels: $(cat $H/fan1_label) / $(cat $H/fan2_label); min $min1/$min2 max $(cat $H/fan1_max)/$(cat $H/fan2_max)"
echo "before:"; show
sudo -v || { echo "sudo failed"; exit 1; }
for t in 3000 4000; do
  echo "set both targets to $t rpm:"
  echo "$t" | sudo tee $H/fan1_target >/dev/null && echo "$t" | sudo tee $H/fan2_target >/dev/null && echo "  write ok" || echo "  write REFUSED"
  for s in 4 8 12; do sleep 4; echo " after ${s}s:"; show; done
done
echo "== done (restore follows), log: $LOG"
