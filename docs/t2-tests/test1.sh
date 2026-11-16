#!/usr/bin/env bash
# Test 1: does the Apple SMC accept a battery charge limit? Restores the original value at the end.
# Run: bash docs/t2-tests/test1.sh   -> writes docs/t2-tests/test1.log
set -u
B=/sys/class/power_supply/macsmc-battery
LOG="$(cd "$(dirname "$0")" && pwd)/test1.log"
exec > >(tee "$LOG") 2>&1
echo "== test1 charge limit  $(date -Is)  kernel $(uname -r)"
show() { echo "  threshold=$(cat $B/charge_control_end_threshold 2>&1) status=$(cat $B/status) capacity=$(cat $B/capacity)% power=$(awk '{printf "%.1f W", $1/1000000}' $B/power_now)"; }
orig=$(cat $B/charge_control_end_threshold)
echo "original:"; show
sudo -v || { echo "sudo failed"; exit 1; }
for v in 80 60 100; do
  echo "write $v:"
  echo "$v" | sudo tee $B/charge_control_end_threshold >/dev/null && echo "  write ok" || echo "  write REFUSED"
  sleep 3; show
done
echo "write 80 and wait 20 s (does charging stop above 80 %?):"
echo 80 | sudo tee $B/charge_control_end_threshold >/dev/null; sleep 20; show
echo "restore original ($orig):"
echo "$orig" | sudo tee $B/charge_control_end_threshold >/dev/null; sleep 2; show
echo "== done, log: $LOG"
