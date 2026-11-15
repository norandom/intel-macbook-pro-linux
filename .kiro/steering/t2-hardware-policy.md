# T2 hardware preservation

The owner has a fresh T2 Linux installation. Preserve its working hardware
support across every port and package operation: kernel and boot configuration,
initramfs modules, driver configuration, firmware/support packages and services,
touch bar, keyboard/trackpad, speakers/microphone, camera, Wi-Fi/Bluetooth and
suspend/resume. Package plans must reject removal or replacement of these
prerequisites. Do not run autoremove or source VM blanket blacklists/purges.

KDE stays installed and dormant as a fallback. Hyprland is a separate full
session, not nested in KDE, and must not start Plasma merely for desktop controls.
Keep the current login manager/configuration. No KDE removal is in scope.

## Observed baseline

Read-only inventory found:
- Running T2 kernel 7.3.4-3-t2-resolute; linux-t2 package 7.3.4-3-resolute,
  matching T2 images/headers for -2 and -3 plus installed generic fallback kernel.
- Boot parameters include intel_iommu=on, iommu=pt, pm_async=off.
- /etc/initramfs-tools/modules explicitly lists t2bce_core, t2bce_dma, t2bce_vhci.
- Loaded modules include t2bce_core/dma/vhci/audio, hid_appletb_kbd,
  hid_appletb_bl, hid_apple, hid_multitouch, apple_gmux, uvcvideo and sound modules.
- apple-firmware-script 1.4-3 and get-apple-firmware.service handle Apple Wi-Fi/
  Bluetooth firmware; preserve package/service and activation relationships.
- apple-t2-audio-config 0.5.3-resolute installs AppleT2 ALSA UCM profiles.
  PipeWire/WirePlumber details are in desktop-audio-policy.md.

Versions describe the observed installation, not new upgrade pins. Preserve
existing repository/update mechanisms; do not freeze normal T2 support updates
or switch to a generic kernel just to build the compositor. Never copy firmware
blobs, machine identifiers or private data into committed specs.

## Verification boundary

Inventory is evidence of configuration/module presence only. The tool session
cannot query the live audio/system buses. Microphone recording, speaker output,
camera capture, touch-bar interaction and suspend/resume acceptance remain live
host checks. Do not claim them verified from package names or module loading.

Capture config hashes/installed package dependencies before a port and compare
afterward. Reject proposed protected-component removals. Preserve both the
Intel-first GPU policy and external-display behavior; capture its custom unit
before reproducing GPU transitions. RDP must not replace normal local audio or
leave physical input/display paths unusable on disconnect.
