# Research & Design Decisions

## Summary

Feature: hyprland-desktop; complex integration; investigated2026-11-15. Source
is norandom/hyperland-forky-worker-vm at
`a1c09ec3f02a98b7c6a4641f907108a2ad080993`. The owner explicitly chose
backporting current source configuration to Ubuntu's native Hyprland0.53.3 and
hyprbars0.53, prioritizing the original decorations. This supersedes the earlier
newer-source-build investigation and its provisional design blocker.

Requirements/design/tasks describe future implementation. No packages, builds,
services, sessions or hardware behavior were changed or tested during research.

## Research Log

### Context and workflows

Read brief, compatibility notes, roadmap, package-policy, desktop-audio-policy,
t2-hardware-policy, protected-system-boundary, desktop-fonts/application-suite
designs, and source defaults. Core product.md/tech.md/structure.md are absent;
no policy was invented to fill them. Applied kiro-spec-init/requirements/design/
tasks and required EARS, requirements/design/task review, design discovery and
synthesis rules; kiro-verify-completion governs final document checks. The batch
-y authorization applies only after actual phase gates pass.

### Actual source evidence

GitHub plugin fetched pinned layouts, snapping, bindings/looknfeel, input/monitor
templates, launcher/appmenu, effects, quota/sparkline, clipboard, keyboard,
shaders, bar styling, Mako/Fuzzel, GTK template, Xfe seed and hostcolor. Snapshot
reads provide complete Waybar template and tasks/desktop.py plus initial
Hyprland/autostart/decorations. Source-inventory.md records exact blob identities.
Attempted tasks/hyprland.py and files/gtk-3.0/settings.ini were incorrect paths;
actual paths are tasks/desktop.py and templates/gtk-3.0/settings.ini.j2.

Source Lua says0.56. It cannot run unchanged on0.53. Source config's actual
behaviors are retained through translation rather than changing the native
compositor generation. No historical decorations.conf is known in this source;
backport current decorations.lua. Original border/hostcolor/style/button intent
is the reference, not an invented older design.

### Native compositor/plugin evidence

Read-only apt-cache show/policy reports Ubuntu26.04 resolute:

| Component | Candidate | Evidence/contract |
| --- | --- | --- |
| hyprland |0.53.3+ds-4 | Provides hyprland-abi-6d24081, hyprland-api-0.1 |
| hyprland-plugin-hyprbars |0.53.0-1 | Depends hyprland-abi-6d24081 |
| uwsm |0.25.2+ds-1 | Native independent-session manager |
| waybar |0.15.0-1 | Full source template module generation |
| mako-notifier |1.10.0-1build1 | Notifications |
| fuzzel |1.12.0+ds-1build1 | Search/picker |
| xdg-desktop-portal-hyprland |1.3.11-1build2 | Native Hyprland portals |
| hyprlock |0.9.2-1build4 | Explicit local lock |
| cliphist |0.5.0-1build1 | Source-compatible runtime clipboard history |
| xwayland |2:24.1.10-1 | Already installed candidate |

The ABI dependency token is concrete evidence for choosing the packaged pair.
Installation must still validate package origin/plan/scripts/triggers and actual
loaded-plugin identity. Resolve package-owned plugin path by dpkg file inventory;
never import source's hardcoded Debian path. No hyprpm plugin rebuild/source
compiler/kernel headers are required. hyprland-guiutils has no candidate and is
not a prerequisite for the source desktop actions implemented here.

### Primary old-version API evidence

Fetched official immutable-version source:

- [0.53.3 example configuration](https://github.com/hyprwm/Hyprland/blob/v0.53.3/example/hyprland.conf): fragment sourcing, conf blocks, bind/bindm, physical monitors and input.
- [0.53.3 dispatcher implementation](https://github.com/hyprwm/Hyprland/blob/v0.53.3/src/managers/KeybindManager.cpp): exact supported command names, fullscreen mode, address-targeted geometry and setprop.
- [0.53.3 HyprCtl](https://github.com/hyprwm/Hyprland/blob/v0.53.3/src/debug/HyprCtl.cpp): JSON clients/monitors/cursor, getprop, keyword, batch and dispatch handling.
- [0.53.3 ConfigManager](https://github.com/hyprwm/Hyprland/blob/v0.53.3/src/config/ConfigManager.cpp): snap, layout, shader keywords and reload events.
- [0.53.3 EventManager](https://github.com/hyprwm/Hyprland/blob/v0.53.3/src/managers/EventManager.cpp): per-instance .socket2.sock event transport.
- [Official0.53 plugin README](https://github.com/hyprwm/hyprland-plugins/blob/64b7c2dff7e5e1fcb4cb7e5db078947744070e1a/hyprbars/README.md): block options/buttons; official pin table maps0.53.3 to this generation.
- [Versioned hyprctl documentation](https://wiki.hypr.land/0.53.0/configuring/using-hyprctl/), [rules](https://wiki.hypr.land/0.53.0/configuring/window-rules/): supplementary0.53-series guidance. Some dispatcher/plugin wiki URLs were unavailable; exact0.53.3 source is the authority where pages differ.

The dispatcher source confirms fullscreen1 means maximized, fullscreen0 true
fullscreen; setfloating/settiled accept window selection; movewindowpixel and
resizewindowpixel parse the command before comma and address selector after it;
setprop takes selector/property/value and supports no_blur and opacity. Native
conf retains nested general.snap, master.mfact and dwindle.default_split_ratio.
JSON clients expose numeric arrays at/size, monitor ID, workspace, floating,
hidden/mapped, class, pinned and fullscreen; Lua object field access must become
validated JSON parsing. Event notifications invalidate snapshots; state queries
remain authoritative. Complete translation matrix is in design.md.

### Decorations fidelity and drift

Plugin0.53 documentation supports the source bar-height/color/text/alignment,
button alignment/padding, double-click, precedence-over-border options and
hyprbars-button entries. Hostcolor generation and active oil-gradient border
translate to native scalar/gradient conf values. The exact mac and win311
styles/buttons are preserved; repeated reload must clear/recreate buttons once.
Plugin source/version differences are tested using the actual Ubuntu pair;
API presence is evidence for design, not a claim of visual acceptance.

### Protected host, input and audio

Host package operations must use foundation policy, including maintainer-script
and trigger review; unknown protected effects block their transaction. No
cryptsetup/LUKS/LVM, fstab/swap/resume, kernels/headers/modules, bootloader,
initramfs/mkinitcpio changes, regeneration or hooks. No global upgrade/autoremove.
No GPU reproduction, RDP VM rendering/output/input branches or remote audio
routing. Preserve T2 support and native AppleT2 UCM/PipeWire/WirePlumber. KDE
remains installed dormant; SDDM authentication/defaults unchanged; no Plasma
runtime/plasma-pa needed. Missing GPU-unit evidence only leaves related GPU
transition validation pending. Live audio/system bus is unavailable here.

Source group_data/all.py verifies de,us; mac_nodeadkeys,;
compose:caps,shift:both_capslock_cancel,altwin:swap_ralt_rwin,lv3:lalt_switch.
Preserve source Super/Command/Option behavior and verify Option+L=@ on the T2
keyboard. No /etc/default/keyboard, console, LUKS or initramfs remapping.

## Architecture Pattern Evaluation

| Option | Decision | Reason |
| --- | --- | --- |
| Copy source Lua into Ubuntu0.53 | Rejected | Incompatible generation |
| Build newer compositor/private library closure | Superseded by explicit owner choice | Unnecessary toolchain/ABI management for chosen port |
| Native0.53 conf + one IPC worker | Selected | Direct decorations translation; native dispatch/state can express source behavior |

## Design Decisions

Adopt native compositor/plugin/uwsm/Waybar/Mako/Fuzzel and source assets. Port
stateful Lua window callbacks/timers into one bounded session worker, sharing
window snapshots for geometry/snapping rather than spawning polling daemons per
feature. Preserve source algorithms and visible behavior; no Lua compatibility
interpreter or new window manager framework. Use generated owned conf fragments
for selected user modes; user data lives separately and survives provisioning.
Applications/fonts/themes retain their own files, and consumers use explicit
contracts. The obsolete source-build direction is not an implementation blocker
or a new rootless-containers dependency of this chosen design.

## Risks & Mitigations

Native plugin properties may differ subtly: configuration parse + repeated reload
+ real mac/win311 visual/button tests are mandatory. IPC can block the compositor:
bound queries, cache monitors, batch mutations and cap polling to the source
cadence. Monitor/scale transforms and reserved areas require fixtures plus live
display checks. Stale window addresses must never target a newly focused window.
Use explicit address selectors and recheck live identity before mutation.
Clipboard/accounts remain private; no credential collection. Package hooks and
T2 hardware checks remain release gates, not assumed satisfied by apt metadata.

## References

Primary source links above and source-inventory.md are the evidence set.
Consumer-contracts.md records independent theme/font/application contracts and
the finalized session status seam; none implies implementation is deployed.
