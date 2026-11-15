# Brief: laptop-resource-policy

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
Port turbo controls, memory safeguards, justified tuning and laptop service policy.
Cover backlog items P01–P06. Reuse source behavior/assets wherever compatible;
record exceptions explicitly.

## Approach
Port incrementally through the existing local pyinfra foundation, using native
Ubuntu packages or reviewed pinned upstream artifacts. Preserve existing working
configuration and supply meaningful validation and restoration paths.

## Scope
Own no-turbo tmpfiles persistence and the user's exact turbo-on/off/status aliases as a sourced Bash fragment; shell-user-tools owns loading the fragment. Own zram/earlyoom/journal/coredump drop-ins and service policy. Preserve disk swap and hibernation configuration; adapt earlyoom exclusions for Plasma/KWin and Hyprland. Evaluate every source tuning independently instead of applying VM kernel arguments, root SSH/password changes, serial getty, module blacklists or commit=60 root remount. Preserve Bluetooth, power management, CUPS capability; disable Avahi including activation paths; exclude snitchd. No GPU state changes. Exact tuning values must be evidence-backed and reversible; source defaults are candidates, not automatically approved settings.

## Boundary Candidates
One feature owns the files and contracts named in this scope. Cross-feature
configuration must use distinct fragments or explicit consumer contracts.

## Out of Boundary
No Snap/snapd or Flatpak, no source secrets, no autologin, no KDE/display-manager
removal, no snitchd, no VM kernel/boot profile or GPU rendering workarounds.
No unrelated foundation or GPU-policy implementation.

## Upstream / Downstream
- Upstream new specs: none.
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

## Strict protected-system boundary

Read .kiro/steering/protected-system-boundary.md. No cryptsetup/LUKS/LVM,
fstab/swap/resume, kernels/modules/headers, bootloader or initramfs/mkinitcpio
changes or regeneration, including installer/package hooks. Preserve existing
keyboard-presence and encrypted-boot customizations. Read-only inventory is allowed.
