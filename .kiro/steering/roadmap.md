# Roadmap

## Overview
Port the source repository's actual features to the owner's Ubuntu KDE T2 Mac
through uv-managed pyinfra and nvm. Preserve the current laptop and login
baseline while adding a full GPU-backed Hyprland session and original widgets,
themes, user tools and RDP. Source audit and 23 work items are in
`docs/source-port-plan.md`; this roadmap supplies feature ownership.

## Approach Decision
- Chosen: source-led feature specs with separate file ownership and dependency waves.
- Why: preserves the requested source behavior while isolating laptop adaptations.
- Alternatives: one giant VM deploy would import destructive/VM-specific defaults;
  foundation-only work misses the actual port. Neither satisfies the request.

## Scope
- In: P01–P23 source-derived port work, compatible original assets and helpers.
- Out: snapd/Snap/Flatpak, autologin, KDE removal, snitchd, VM software rendering,
  distro conversion, inherited root SSH policy and unrelated private credentials.

## Constraints
Foundation is upstream infrastructure, not the full port. Existing foundation
requirements/design approvals remain recorded; task approval is still pending.
Source revision: a1c09ec3f02a98b7c6a4641f907108a2ad080993.
Fresh-install clarification: preserve the packaged T2 audio stack (AppleT2 UCM,
PipeWire, WirePlumber). Hyprland is standalone; SDDM may remain without a
Plasma runtime. KDE stays installed and dormant as a fallback; no removal is planned.
All specs must preserve T2 hardware support per t2-hardware-policy.md.
Strict no-go: protected-system-boundary.md prohibits cryptsetup/LUKS/LVM, fstab,
kernel/boot and initramfs/mkinitcpio changes, including regeneration hooks.
The GPU unit is missing evidence for GPU reproduction/hardware validation;
independent feature designs may proceed. Runtime acceptance must not be claimed
from document review. Spec batch completion below means documents, not software.

## Boundary Strategy
- Resource policy owns turbo fragment; shell loads it.
- Fonts owns installed fonts/X11 font helper; desktop invokes helper.
- Apps owns native application installers; shell owns user npm/uv tools and nvim;
  containers owns Podman/podman-tui; desktop owns compositor/widgets.
- Themes owns terminal configs, palette targets and theme commands; desktop owns
  its Waybar theme module and consumes those commands/state.
- RDP owns its units/patches, with session contract supplied by desktop.
- Shared root deploy changes belong to foundation/integration work, not concurrent
  feature tasks; feature designs expose optional deploy entry points.

## Existing Spec Updates
- [ ] local-system-foundation -- implement the reviewed execution/package-policy contract; task approval pending. Dependencies: none
- [ ] laptop-gpu-policy -- capture existing custom unit before final reproduction design. Dependencies: none

## Direct Implementation Candidates
None. Turbo controls are included with laptop-resource-policy, loaded by shell.

## Specs (dependency order)
- [x] laptop-resource-policy -- Port turbo controls, memory safeguards, justified tuning and laptop service policy. Dependencies: none
- [x] rootless-containers -- Port rootless Podman, Docker command compatibility and Compose integration. Dependencies: none
- [x] desktop-fonts -- Port public Nerd/Fixedsys fonts and fontconfig integration. Dependencies: none
- [x] application-suite -- Account for every source application and release tool through permitted Ubuntu install routes. Dependencies: none
- [x] shell-user-tools -- Port the source Bash experience, nvim-simple and user developer tooling. Dependencies: laptop-resource-policy, application-suite
- [x] coordinated-themes -- Port all five palettes and coordinated terminal/application theme switching. Dependencies: desktop-fonts, shell-user-tools
- [x] hyprland-desktop -- Port a full native-GPU Hyprland session and the source widgets/helpers alongside KDE. Dependencies: desktop-fonts, application-suite, coordinated-themes
- [x] hyprland-rdp -- Port RDP and validate the assembled native-GPU desktop without VM console assumptions. Dependencies: hyprland-desktop, coordinated-themes, rootless-containers

## Dependency refinement during research

Theme switching owns terminal/editor assets and can work without a running
compositor; Waybar signal and Hyprland notifications are optional consumer
integrations. Therefore coordinated-themes does not depend on completion of
hyprland-desktop. Both share the source CLI/state contract. The owner subsequently chose to backport the newer source configuration to
Ubuntu's packaged Hyprland rather than build a newer compositor. Desktop does
not depend on rootless-containers for a builder. No reciprocal dependency is introduced.

## Compositor direction: explicit owner decision

Use Ubuntu's packaged Hyprland 0.53.3+ds-4 and compatible packaged hyprbars.
Backport the source Lua/config/IPC behavior to that release's interfaces.
Prioritize the original decorations, which the owner had ported forward to newer
Hyprland. Do not pursue a newer compositor build or its dependency closure.
Keep the full source feature inventory, with explicit per-feature backport
mapping and honest validation status rather than a blanket build blocker.

The native desktop backport consumes the themes-owned terminal/theme CLI from
its launcher and Waybar controls. Its final design therefore follows the theme
spec's finalized producer contract. Desktop version/API investigation already
underway remains discovery input; dependent design finalization follows the
refined graph. Themes do not require a running compositor.

## RDP package direction: explicit owner decision

Use upstream MuNeNiCK/hypr-rdp GitHub release archive. No fork .deb, patch port
or local RDP rebuild. Validate upstream declared compositor support against the
native0.53.3 desktop; report unsupported/unverified behavior honestly without
reintroducing a newer compositor build or source-RDP fallback.

## Deferred backlog

- [ ] Craft suite -- use the source installer when reopened; all7artcraft_apps entries deferred.
- [ ] LibreOffice -- Writer/Calc, language support, tabbed UI and Carlito deferred.

Details: docs/backlog.md. Neither item is current implementation work or a
missing dependency for the Hyprland/decorations port.

## Specification batch result

All eight new source-port specs have requirements, designs and unchecked
implementation tasks. Independent cross-spec review passed after one repair
round. Checked boxes above mean specification documents completed, not software
installed or runtime acceptance passed. Existing foundation task approval and
GPU evidence follow-up remain listed separately. No implementation was performed.
