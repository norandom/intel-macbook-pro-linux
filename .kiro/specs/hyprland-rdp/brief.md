# Brief: hyprland-rdp

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
Port RDP and validate the assembled native-GPU desktop without VM console assumptions.
Cover backlog items P21–P23. Reuse source behavior/assets wherever compatible;
record exceptions explicitly.

## Approach
Port incrementally through the existing local pyinfra foundation, using native
Ubuntu packages or reviewed pinned upstream artifacts. Preserve existing working
configuration and supply meaningful validation and restoration paths.

## Scope
Own upstream maintainer release-archive selection/version/checksum, supported current configuration/hooks, adapted session helpers and RDP-only units. Do not port fork patches or build locally. Scope activation to Hyprland, not generic graphical-session that starts in KDE. Preserve local display, lock behavior, audio and keyboard when client connects/disconnects. Assess away.py explicitly; do not automatically apply source sudo/ptrace policy. Authentication/network exposure need an explicit safe operator configuration before enabling listener; do not assert unknown user intent as a requirement. Own final assembled port validation checklist consuming other feature checks, not their implementations. Missing GPU unit must remain an explicit blocker for actual GPU state reproduction and attach/detach tests. No software-rendering forcing or VM-only output blanking. If exact upstream/runtime compatibility or behavior is not established, report a bounded gate instead of inventing working APIs.

## Boundary Candidates
One feature owns the files and contracts named in this scope. Cross-feature
configuration must use distinct fragments or explicit consumer contracts.

## Out of Boundary
No Snap/snapd or Flatpak, no source secrets, no autologin, no KDE/display-manager
removal, no snitchd, no VM kernel/boot profile or GPU rendering workarounds.
No unrelated foundation or GPU-policy implementation.

## Upstream / Downstream
- Upstream new specs: hyprland-desktop, coordinated-themes, rootless-containers.
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

## Owner decision superseding fork/source-build work

Use upstream MuNeNiCK/hypr-rdp GitHub release package, not the norandom patched
.deb and not a local RDP rebuild. Read upstream-release-notes.md for candidate
v0.1.8 asset/digest and the documented0.54+ versus selected0.53.3 discrepancy.
Do not assume compatibility or silently replace the compositor/build a fork.
Retain necessary source behavior through supported upstream configuration/hooks;
many source workarounds may now be upstream and should not be copied blindly.

Existing native-GPU desktop version/ABI and lifecycle contracts are in
hyprland-desktop/design.md and consumer-contracts.md once finalized. Use exact
contracts; do not import source eval/Lua calls into0.53. Package dependency and
activation checks must honor all protected-system/T2 policies. If FUSE or another
optional kernel interface is unavailable, report the capability pending rather
than loading/rebuilding/replacing hardware/kernel modules.
