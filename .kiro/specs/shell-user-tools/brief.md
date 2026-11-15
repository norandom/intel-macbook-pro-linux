# Brief: shell-user-tools

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
Port the source Bash experience, nvim-simple and user developer tooling.
Cover backlog items P10–P13. Reuse source behavior/assets wherever compatible;
record exceptions explicitly.

## Approach
Port incrementally through the existing local pyinfra foundation, using native
Ubuntu packages or reviewed pinned upstream artifacts. Preserve existing working
configuration and supply meaningful validation and restoration paths.

## Scope
Own grml Bash fragment, readline/history/completions; nvim-simple pinned config with backup and plugins; npm developer tools under nvm (pnpm, Aikido Safe Chain, Copilot, Codex, ccusage), uv euporie/kernel and agent skill installers, ax/completions. Own optional rclone mount configuration, cache cleanup helper/timer and Quarto Python/TinyTeX options with explicit prerequisites and dispositions. No source credentials/licenses. Resource spec owns turbo-alias fragment; this spec sources it. Theme spec owns Neovim theme bridge and terminal/editor palette integration; avoid editing each other's files. Node Bash block remains foundation-owned: use a distinct marked block. Standalone tools work in KDE without Hyprland. Review Safe Chain wrapper/PATH conflicts and avoid automatic destructive cache cleanup.

## Boundary Candidates
One feature owns the files and contracts named in this scope. Cross-feature
configuration must use distinct fragments or explicit consumer contracts.

## Out of Boundary
No Snap/snapd or Flatpak, no source secrets, no autologin, no KDE/display-manager
removal, no snitchd, no VM kernel/boot profile or GPU rendering workarounds.
No unrelated foundation or GPU-policy implementation.

## Upstream / Downstream
- Upstream new specs: laptop-resource-policy, application-suite.
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
