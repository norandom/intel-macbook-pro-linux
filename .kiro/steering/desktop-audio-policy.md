# Desktop and T2 audio policy

The owner clarified that this is a fresh T2 Linux install and wants a full
Hyprland desktop, with no Plasma session running within it. There is no need
to retain KDE components merely to provide Hyprland functionality. SDDM can
remain the standalone login screen. The owner subsequently confirmed KDE stays installed and dormant as a
fallback; KDE removal is out of scope.

Keep existing login authentication/default behavior until the planned Hyprland
session is verified. This supersedes any implication that KDE services must run
inside Hyprland. Retaining KDE as a temporary fallback is not a runtime dependency
of the new desktop.

Preserve the newly installed T2 audio stack and its package-owned configuration:
- apple-t2-audio-config 0.5.3-resolute, including AppleT2 ALSA UCM profiles under
  /usr/share/alsa/ucm2/AppleT2 and conf.d/AppleT2x2, AppleT2x4, AppleT2x6.
- PipeWire 1.6.2 and pipewire-pulse/pipewire-alsa integration.
- WirePlumber 0.5.13 for session/device policy.
- Bluetooth capability and audio support.

These versions were observed through local dpkg metadata, not selected as new
upgrade pins. No audio package was installed/removed by this inspection. The
live PipeWire/session bus is inaccessible from the tool environment; no speaker,
mic, route or volume behavior is claimed verified.

Hyprland owns its Waybar audio controls and a standalone configuration UI choice
if required. It must not require plasma-pa or launch Plasma for volume control.
Retain package-owned ALSA UCM profiles, T2 kernel/support and audio policy when
planning any future KDE removal. Do not copy source VM RDP audio rerouting into
normal local laptop operation. RDP integration must restore prior local routing.
