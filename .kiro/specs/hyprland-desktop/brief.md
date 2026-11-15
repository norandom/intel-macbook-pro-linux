# Brief: hyprland-desktop

## Problem
The owner wants the actual features of norandom/hyperland-forky-worker-vm
ported to their Ubuntu KDE T2 Mac laptop. The prior foundation-only task plan
did not deliver this capability.

## Current State
uv/pyinfra/nvm baseline exists. The source is audited at revision
`a1c09ec3f02a98b7c6a4641f907108a2ad080993`; source modules inspected are available
under `/tmp/t2-source-audit` for this session, with provenance in
`.kiro/source-repository-index.json`. The backlog is `docs/source-port-plan.md`.
There is no local implementation of this feature yet.

## Desired Outcome
Port a full native-GPU Hyprland session and the source widgets/helpers alongside KDE.
Cover backlog items P14–P18. Reuse source behavior/assets wherever compatible;
record exceptions explicitly.

## Approach
Port incrementally through the existing local pyinfra foundation, using native
Ubuntu Hyprland0.53.3 and ABI-matched hyprbars0.53; backport newer source
configuration/helpers, prioritizing the original decorations. Preserve existing working
configuration and supply meaningful validation and restoration paths.

## Scope
Own compatible Hyprland/config/hyprbars version contract, separate selectable full SDDM/uwsm session preserving login screen/default/authentication and KDE. Source is newer Lua API with hardcoded Debian ABI/plugin path: translate to native0.53 conf/IPC and discover package-owned plugin path. Own monitor/input/layout/snapping/decorations, original Waybar widgets (entire template), hostcolor generation, appmenu/fuzzel/mako, GTK/Xfe seed, clipboard tools/services/night shaders, hypr-launch, layout/kbd/pin/glass/shadow/deco helpers, quota/sparklines and session lifecycle. Do not force software rendering, VM outputs or RDP-presence initial lock. Font spec owns X11 font helper; this spec calls it. Theme spec owns hypr-term/hypr-termtheme and terminal configs/palettes; desktop widgets call stable theme contract. Define that contract without writing theme-owned files. Resource GPU policy is preserve-existing: missing GPU unit blocks reproduction/hardware-transition validation only, not all desktop discovery; do not invent a replacement GPU mechanism. No RDP unit management here. Laptop battery/Bluetooth UI are candidate additions, not falsely claimed source features.

## Boundary Candidates
One feature owns the files and contracts named in this scope. Cross-feature
configuration must use distinct fragments or explicit consumer contracts.

## Out of Boundary
No Snap/snapd or Flatpak, no source secrets, no autologin, no KDE/display-manager
removal, no snitchd, no VM kernel/boot profile or GPU rendering workarounds.
No unrelated foundation or GPU-policy implementation.

## Upstream / Downstream
- Upstream new specs: desktop-fonts, application-suite.
- Foundation is an existing upstream execution/package-policy contract.
- GPU policy is an adjacent preservation constraint; its missing existing unit
  must not be guessed or turned into a blocker for unrelated feature design.
- Downstream consumers follow the project roadmap dependency order.

## Existing Spec Touchpoints
- Extends: none; this is a separate feature seam.
- Adjacent: local-system-foundation and laptop-gpu-policy.

## Constraints
English specs. Source paths/API compatibility must be verified against the
pinned source; source settings are not proof of Ubuntu compatibility. Specs
record actual research and tests separately from planned validation. Follow
Kiro phase reviews; batch uses documented fast-track design/tasks mode.

## Fresh-install and audio clarification

The owner has a new T2 install, requires its T2 audio stack, and does not need
KDE/Plasma running inside Hyprland. Read .kiro/steering/desktop-audio-policy.md.
Preserve apple-t2-audio-config ALSA UCM, PipeWire and WirePlumber; provide native
Hyprland/Waybar volume controls. SDDM may remain as a login manager without
Plasma. KDE stays installed and dormant as a fallback; no removal is planned.

Read .kiro/steering/t2-hardware-policy.md: preserve T2 kernel/initramfs/modules,
firmware, touch bar, speakers/microphone, camera, keyboard/trackpad, Wi-Fi/
Bluetooth and suspend/resume. Inventory presence is not live acceptance.

## Strict protected-system boundary

Read .kiro/steering/protected-system-boundary.md. No cryptsetup/LUKS/LVM,
fstab/swap/resume, kernels/modules/headers, bootloader or initramfs/mkinitcpio
changes or regeneration, including installer/package hooks. Preserve existing
keyboard-presence and encrypted-boot customizations. Read-only inventory is allowed.

Read .kiro/steering/keyboard-policy.md: preserve source Super mapping and
German Mac graphical layout; verify Option+L=@. No protected boot/unlock input changes.

## Owner decision superseding newer-build investigation

The owner explicitly chose backporting the configuration to Ubuntu's packaged
Hyprland rather than building a newer version. Prioritize the original
decorations: the owner had ported them forward to new Hyprland. Use native
0.53.3+ds-4 with the matching packaged hyprbars ABI; translate Lua configuration
and helper IPC to the supported older interfaces. The newer-stack dependency
closure is no longer a prerequisite. Preserve source visual/interaction intent
and track any feature-specific adaptations rather than block the entire port.

## Final direction

The owner selected config backporting, not a newer compositor build. Native0.53
decorations/controls are first; keep the complete source desktop feature scope.
Preserve exact source Super/Command/Option mapping and German Mac Option+L=@
inside the graphical session only. Protected boot/storage/keyboard-decryption
setup must remain untouched. Themes is an independent upstream CLI/state
producer; desktop consumes its approved contract.
