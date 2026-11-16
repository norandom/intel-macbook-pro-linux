#!/usr/bin/env bash
# Test 3: where does hibernation hang? Uses the kernel's pm_test: each level runs hibernation up to
# that stage, waits 5 s, then comes back WITHOUT powering off. Nothing is unloaded or changed
# permanently; pm_test is reset to "none" at the end.
#   bash docs/t2-tests/test3.sh          -> docs/t2-tests/test3.log
#   bash docs/t2-tests/test3.sh nowifi   same, with the Wi-Fi driver (brcmfmac) unloaded first and
#                                     reloaded at the end (Wi-Fi drops for ~30 s)
#   bash docs/t2-tests/test3.sh shutdown disk mode "shutdown" instead of "platform": the kernel
#                                     skips the firmware's ACPI S4 calls (restored at the end)
# If the machine hangs: hold the power button, boot, then run
#   journalctl -b -1 -k | grep -E 'PM:|Freezing|suspend|t2bce|brcmf|amdgpu' | tail -40 >> docs/t2-tests/test3.log
# and tell Claude. The log line before the hang names the stage.
# Save your work first.
set -u
LOG="$(cd "$(dirname "$0")" && pwd)/test3.log"; mode=${1:-normal}
exec > >(tee -a "$LOG") 2>&1
log() { echo "$(date +%T) $*"; sync; }
echo "== test3 hibernate stages ($mode)  $(date -Is)  kernel $(uname -r)"
sudo -v || exit 1
echo "pm_test levels: $(cat /sys/power/pm_test)   disk modes: $(cat /sys/power/disk)"
cleanup() {
  echo none | sudo tee /sys/power/pm_test >/dev/null
  [ "$mode" = shutdown ] && { echo platform | sudo tee /sys/power/disk >/dev/null; log "disk mode back to: $(cat /sys/power/disk)"; }
  if [ "$mode" = nowifi ]; then sudo modprobe brcmfmac && sudo modprobe brcmfmac_wcc 2>/dev/null; log "brcmfmac reloaded"; fi
  log "pm_test reset to: $(cat /sys/power/pm_test)"
}
trap cleanup EXIT
if [ "$mode" = nowifi ]; then
  sudo modprobe -r brcmfmac_wcc brcmfmac && log "brcmfmac unloaded" || log "brcmfmac unload FAILED"
fi
if [ "$mode" = shutdown ]; then
  echo shutdown | sudo tee /sys/power/disk >/dev/null && log "disk mode: $(cat /sys/power/disk)"
fi
for level in freezer devices platform processors core; do
  log "start level=$level"
  echo "$level" | sudo tee /sys/power/pm_test >/dev/null
  if echo disk | sudo tee /sys/power/state >/dev/null 2>&1; then log "PASS  level=$level"
  else log "FAIL  level=$level (returned an error, see dmesg below)"; break; fi
  sleep 3
done
echo "--- kernel messages of this test:"
sudo dmesg | grep -E 'PM:|Freezing|Restarting|suspend|hibernat|t2bce|brcmf|amdgpu' | tail -40
echo "== done"
