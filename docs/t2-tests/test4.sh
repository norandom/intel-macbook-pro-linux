#!/usr/bin/env bash
# Test 4: can the T2 bridge drivers (t2bce_*) be unloaded and loaded again in a running session,
# with keyboard, trackpad, Touch Bar and audio coming back? That's what hibernate needs (the T2
# chip is power-cycled while the Mac is off). Audio (PipeWire) is stopped first, because it holds
# t2bce_audio open; no force-unload.
#   bash docs/t2-tests/test4.sh   -> docs/t2-tests/test4.log
# During the test keyboard and trackpad are gone for ~10 s; that's expected. If they don't come
# back within a minute: power off with the button, boot, and tell Claude (log is on disk).
# An external USB keyboard or an SSH login over Tailscale is a good fallback to have ready.
set -u
LOG="$(cd "$(dirname "$0")" && pwd)/test4.log"
exec > >(tee -a "$LOG") 2>&1
log() { echo "$(date +%T) $*"; sync; }
echo "== test4 t2bce unload/reload  $(date -Is)  kernel $(uname -r)"
sudo -v || exit 1
lsmod | grep -E '^t2bce|^hid_appletb' | awk '{print "  before: " $1 " used by " $3}'
log "stop audio (user services; EasyEffects and the filter chain first, they crash otherwise)"
clients=$(for c in easyeffects.service filter-chain.service; do systemctl --user -q is-active "$c" && echo "$c"; done)
[ -n "$clients" ] && systemctl --user stop $clients
systemctl --user stop pipewire-pulse.socket pipewire.socket pipewire-pulse.service wireplumber.service pipewire.service 2>&1
sleep 1
# One sudo call for the whole unload/reload, so it can't stop half-way waiting for a password.
sudo sh -c '
  log() { echo "$(date +%T) $*"; sync; }
  log "unload t2bce_audio t2bce_vhci t2bce_core t2bce_dma"
  if modprobe -r t2bce_audio t2bce_vhci t2bce_core t2bce_dma; then log "unloaded"; else log "UNLOAD FAILED (nothing forced)"; fi
  sleep 3
  log "load t2bce_vhci t2bce_audio (pulls in core + dma)"
  modprobe t2bce_vhci; modprobe t2bce_audio
  log "loaded: $(lsmod | grep -c ^t2bce) t2bce modules"
'
sleep 5
log "start audio"
systemctl --user start pipewire.socket pipewire-pulse.socket wireplumber.service 2>&1
sleep 2; [ -n "$clients" ] && systemctl --user start $clients
sleep 3
lsmod | grep -E '^t2bce|^hid_appletb' | awk '{print "  after: " $1 " used by " $3}'
echo "  input devices: $(hyprctl devices -j 2>/dev/null | jq '[.keyboards[].name, .mice[].name] | map(select(test("apple|trackpad"; "i"))) | length') Apple keyboard/trackpad entries"
echo "  audio sinks: $(wpctl status 2>/dev/null | sed -n '/Sinks:/,/Sources:/p' | grep -c '\.')"
sudo dmesg | grep -E 't2bce|appletb|apple' | tail -20
log "done: does the keyboard type, the trackpad move, the Touch Bar show keys, audio play?"
