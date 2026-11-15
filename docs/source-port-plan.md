# Source repository port plan

Source: [norandom/hyperland-forky-worker-vm](https://github.com/norandom/hyperland-forky-worker-vm),
revision `a1c09ec3f02a98b7c6a4641f907108a2ad080993`.
The complete file tree, README sections, deploy order, all task modules, defaults,
and selected compositor/widget/build integration files were inspected.
`.kiro/source-repository-index.json` records file identities and inspection scope.
Individual helper scripts/assets still need detailed compatibility review during
port design; a file-tree inventory is not a runtime compatibility test.

This is the missing source-derived port backlog. The foundation's existing
11 tasks deliver infrastructure only and do not represent completion of this
port. The eight feature specs and their implementation plans are now generated;
see the Kiro roadmap and portfolio review. These are not installed features. Preserve prior foundation/GPU approvals within their boundaries.

## Source task coverage

| Source module | Port disposition |
| --- | --- |
| apt_forky | Exclude distro conversion, source replacement and full upgrade; retain Ubuntu and strict no Snap/Flatpak policy. |
| base | Reuse CLI selection; exclude desktop/display-manager purge and VM agent. |
| memory | Adapt zram/reclaim, earlyoom and journal/core limits for the laptop. |
| tuning | Evaluate individually; no wholesale VM boot, root-SSH or blacklist port. |
| services | Adapt: preserve Bluetooth/power/printing; disable Avahi; exclude guest agent. |
| containers | Port rootless Podman, Compose compatibility and user integration. |
| fonts | Port Nerd/Fixedsys fonts and fontconfig, preserving existing fonts. |
| apps | Inventory all native apps/release tools; select compatible install routes and distinguish role-specific extras. |
| user_tools | Port developer tools, nvim-simple and related helpers; adapt npm to nvm. |
| shell | Port Bash/readline/history/completion and terminal integration; add turbo controls. |
| desktop | Port full session, original desktop UI and helpers alongside KDE. |
| themes | Port five palettes and application synchronization. |
| hypr_rdp | Port native-GPU-compatible RDP integration; review each patch/helper. |
| autologin | Excluded explicitly. Existing login and default session retained. |
| snitchd | Excluded explicitly; no firewall service/rules/trial unit imported. |
| away | Evaluate separately: source RDP-presence lock changes sudo/ptrace policy; do not import VM unattended-session behavior automatically. |
| private | Inventory optional private fonts/licenses workflow; do not copy source secrets or overwrite local licenses. |

## Latest owner constraints

KDE stays installed and dormant as a fallback. Preserve the fresh T2 hardware
stack, including touch bar, microphone/camera, Apple audio, input and firmware.
German Mac graphical input must produce Option+L=@ while retaining the source
Super mapping. No protected boot/unlock keyboard changes.

Strict no-go: cryptsetup/LUKS/LVM, fstab/swap/resume, kernels/modules/headers,
bootloader and initramfs/mkinitcpio customizations/artifacts. No direct writes,
regeneration or indirect package-trigger changes. See protected-system-boundary.md
and other steering policies. This supersedes any earlier implication that
filesystem/kernel tuning could be adopted after evaluation; it is excluded.

## Port tasks

Every item includes a source seam and an observable deliverable. Work uses the
foundation's package policy and retains Intel-first graphics, KDE and existing
login. None may use Snap or Flatpak, including Ubuntu transition packages.

### Laptop controls and resource management

- [ ] P01 Port turbo persistence and shell controls.
  - Source: user-provided tmpfiles rule and exact turbo-on/off/status aliases;
    integrate with source `tasks/shell.py` rather than replace .bashrc.
  - Done: boot default reads no_turbo=1, all three aliases work, and nvm remains available.
- [ ] P02 Port zram with the existing disk swap retained.
  - Source: `tasks/memory.py`, zram defaults in `group_data/all.py`.
  - Adapt size/algorithm/priority to 64 GB RAM and hibernation requirements;
    avoid live swap recreation under pressure.
  - Done: intended devices/priorities and memory-pressure behavior verified.
- [ ] P03 Port earlyoom with KDE and Hyprland protection.
  - Source: `tasks/memory.py`, `files/system/earlyoom`.
  - Evaluate browser preference and any existing OOM manager.
  - Done: effective thresholds/process rules protect both desktop stacks.
- [ ] P04 Port journald and coredump storage limits.
  - Source: `files/system/journald.conf`, `coredump.conf`.
  - Source values: journal 500M/100M, coredump MaxUse=500M, KeepFree=1G;
    identify the actual Ubuntu crash handler before applying coredump settings.
  - Done: effective limits and applicable handler are reported and verified.
- [ ] P05 Evaluate and port justified development tuning.
  - Source: `tasks/tuning.py`, `files/system/99-memory.conf`, `90-net.conf`.
  - Produce accept/reject decisions for reclaim, dirty-writeback, BBR/fq,
    buffers and file/inotify limits. Filesystem/boot/kernel changes are no-go. Keep T2 boot arguments;
    omit haltpoll, mitigations=off, audit=0, root-password SSH, serial console,
    blanket blacklists and automatic commit=60 root remount.
  - Done: each adopted setting has a host-specific rationale, effective-state
    check and rollback; rejected settings remain absent from managed changes.
- [ ] P06 Port laptop service policy.
  - Source: `tasks/services.py` and disabled_units defaults.
  - Preserve Bluetooth, laptop power management and CUPS capability; disable
    Avahi including activation paths. Exclude QEMU agent and snitchd.
  - Done: effective service states match policy, Bluetooth works, and printing
    remains configurable without relying on mDNS discovery.

### Containers, fonts, applications and shell

- [ ] P07 Port rootless Podman and Compose compatibility.
  - Source: `tasks/containers.py`.
  - Check Ubuntu packages, subuid/subgid, existing Docker conflicts, short-name
    resolution, docker/docker-compose compatibility, user API socket, linger
    and CPU weight instead of assuming VM defaults fit.
  - Done: a rootless container and Compose project run as the desktop user;
    adopted lifecycle behavior is verified without a privileged Docker daemon.
- [ ] P08 Port Nerd Fonts, Fixedsys and fontconfig.
  - Source: `tasks/fonts.py`, `templates/fontconfig/fonts.conf.j2`, font pins.
  - Reuse checksum verification, JetBrainsMono/FiraCode, extra public fonts and
    X11 core-font setup; distinguish optional private fonts.
  - Done: expected families/glyphs resolve in terminals, widgets and Xwayland.
- [ ] P09 Port the application/release-tool manifest for Ubuntu.
  - Source: `tasks/apps.py`, release_tools and client-role defaults.
  - Account for deferred office/localization and active/optional browsers, editors, terminal/file utilities,
    downloads/sync, GUI tools and release binaries; classify role-specific
    Quarto/Positron/VS Code/ArtCraft apps explicitly rather than silently omit them.
  - Replace Debian-only artifacts with reviewed compatible builds; Chromium is
    a specific Ubuntu Snap-transition risk. Do not inherit source app purges.
  - Done: a source-to-local package matrix shows a compatible install route or
    explicit pending/excluded status for every source application.
- [ ] P10 Port nvim-simple, not merely the Neovim package.
  - Source: `tasks/user_tools.py`, pinned norandom/nvim-simple revision,
    `files/nvim/plugin/debian-hypr-theme.lua`.
  - Preserve/back up existing config; port CUA keys, menus, quickui, airline,
    NERDTree/devicons and Berg light/dark behavior. Surface plugin failures.
  - Done: editor configuration/plugins and theme switching work interactively.
- [ ] P11 Port user developer/agent/notebook tooling.
  - Source: `tasks/user_tools.py` and version/checksum defaults.
  - Account for pnpm, Aikido Safe Chain, Copilot, Codex, ccusage, euporie with
    kernel, pretty-mermaid skills, ax and completions. Use nvm-owned npm globals
    and uv environments; evaluate wrapper/PATH interactions.
  - Done: source tools have local version/install/auth status and smoke checks;
    missing credentials remain explicit setup steps, never copied secrets.
- [ ] P12 Port sync mounts, cache helper and client extras as distinct options.
  - Source: rclone user services, dev-disk-reclaim/helper timer, Quarto Python
    and TinyTeX sections in `tasks/user_tools.py`; `tasks/private.py`.
  - Inventory expected remotes/private assets first; keep cache cleanup dry-run
    behavior and review timer/resource effects before enabling them.
  - Done: each optional integration has an explicit disposition; enabled options
    verify their prerequisites and do not delete unrelated data.
- [ ] P13 Port the source Bash and readline experience.
  - Source: `tasks/shell.py`, `files/bash/grml.bash`.
  - Reuse prompt/aliases/functions, directory stack, shared timestamped history,
    prefix Up/Down and completions; integrate P01 and nvm without duplicate PATH
    entries. Review source token-export and uutils substitutions separately.
  - Done: interactive behavior survives repeat provisioning and existing local
    shell customizations remain intact.

### Full Hyprland session and original desktop features

- [ ] P14 Establish compatible Hyprland/plugin/config versions and session entry.
  - Source: `tasks/desktop.py`, `files/hypr/hyprland.lua`, decorations.lua,
    Lua configuration modules and uwsm integration.
  - Source uses Lua configuration and an ABI-locked Debian hyprbars plugin;
    backport to the native Ubuntu 0.53.3 config/IPC and matching hyprbars, prioritizing the owner's decorations; no newer compositor build.
  - Add a full selectable session through existing SDDM; preserve default login,
    Intel-first graphics and KDE. No nested desktop or tty autologin.
  - Done: owner can select either desktop and return to the existing login.
- [ ] P15 Port monitors, input, layouts, snapping and decorations.
  - Source: monitor/input templates, bindings/layouts/looknfeel/aerosnap/
    cursorzone/decorations modules, `tools/hostcolor.py`; hypr-layout, hypr-kbd,
    hypr-deco, hypr-pin, hypr-glass and hypr-shadow helpers.
  - Replace VM/headless output assumptions with internal/external display
    behavior; retain Apple keyboard support. Respect the existing GPU unit.
  - Done: keyboard/layout controls, snapping, titlebar buttons and host colors
    work on the compatible compositor without VM rendering patches.
- [ ] P16 Port the original Waybar widgets and launch behavior.
  - Source: Waybar template/style/icon, hypr-launch, hypr-sparkline,
    hypr-agent-quota and widget command dependencies.
  - Include app/terminal/browser/file launchers, window list, clock, CPU/MEM/net
    graphs, AI quota, volume drawer, tray, submap badge, layout, clipboard,
    night filter, theme, keyboard and power controls.
  - Adapt app paths and absent quota credentials; assess battery/Bluetooth
    integration as laptop additions rather than source features.
  - Done: each widget renders and acts correctly, launched apps survive bar
    reload, and Waybar does not start automatically in KDE.
- [ ] P17 Port the app menu, notifications, launcher and file-manager styling.
  - Source: hypr-appmenu, fuzzel, mako, Xfe seed config, desktop entries,
    `files/hypr/autostart.lua` and GTK settings.
  - Reuse the source visual behavior; verify GTK layer-shell dependencies and
    preserve user changes after initial seed. Optional retro icon assets need
    their own provenance/disposition.
  - Done: app/search/power menus and notifications work in Hyprland with no
    automatic VM-console lock on a normal authenticated login.
- [ ] P18 Port clipboard integration and night-filter effects.
  - Source: hypr-cliphist, hypr-clip-bridge, clipboard recorder/wipe units,
    hypr-nightmode and green/dark shaders.
  - Scope services to Hyprland; review RAM storage, nightly wipe and X11
    STRING-to-UTF-8 bridging. Check GPU shader API compatibility.
  - Done: copy/paste/history and effect switching work locally without polluting
    KDE service startup or requiring an RDP client.

### Themes and terminal integration

- [ ] P19 Port all five palettes and theme generation assets.
  - Source: cobalt/navy/fixedsys/cream/petrol files, `tools/themegen.py`,
    `tools/vscodetheme.py`, `tasks/themes.py`.
  - Include btop, Claude, Sublime, Ghostty/tab CSS, foot and VS Code/Positron
    themes; track Chromium policy and optional installed applications explicitly.
  - Done: all five palettes retain source colors/fonts and selected application
    themes load without replacing unrelated settings.
- [ ] P20 Port coordinated terminal and editor theme switching.
  - Source: hypr-termtheme, hypr-term, Terminator config/theme_menu plugin,
    Ghostty/foot configs, xfce4-terminal settings and Neovim theme bridge.
  - Preserve per-profile selection and UI controls; distinguish Hyprland
    compositor tint/effects from any future KDE decoration adaptation.
  - Done: terminal profile changes update supported installed tools and the
    Waybar indicator; unsupported/missing apps do not break switching.

### Native-GPU RDP and end-to-end port validation

- [ ] P21 Use the upstream maintainer's hypr-rdp release package.
  - Source: MuNeNiCK/hypr-rdp GitHub releases; candidate v0.1.8 x86_64 archive,
    with source-repository RDP settings treated as behavior references only.
  - Verify immutable release URL/SHA256, ELF/runtime dependencies and behavior
    on Ubuntu's0.53.3 compositor. Upstream README declares0.54+; upstream source
    has a tested legacy monitor-IPC fallback, which is not full compatibility proof.
  - Do not use the fork .deb, port fork patches or rebuild either RDP/compositor.
  - Done: reviewed release binary is installed only through its permitted route,
    and runtime compatibility is verified or explicitly pending/unsupported.
- [ ] P22 Port session-scoped RDP behavior for a physical laptop.
  - Source: RDP templates/helpers as references, using current upstream hooks
    instead of inheriting obsolete log parsing and monitor workarounds; `tasks/away.py`, `docs/away-lock.md` as assessment inputs.
  - Review bind/authentication, keyboard, clipboard/files/audio, reconnect and
    display-size memory. Adapt console locking, monitor blanking and sound
    routing; do not import VM-specific display or sudo/ptrace policy blindly.
  - Done: RDP connects to Hyprland, disconnect/reconnect preserves usable local
    display/audio/input, and its services do not attach to KDE.
- [ ] P23 Validate the assembled port and replay safety.
  - Depends on adopted feature implementations; no hardware-state tests until
    the existing GPU setup is captured.
  - Verify cold boot, login/session selection, local widgets/themes/tools,
    rootless containers, Bluetooth, printer capability, suspend/resume,
    display attach/detach and remote access under the agreed GPU policy.
  - Done: a repeated deploy preserves user data/config and reports no changes
    for matching state; every requested feature is verified or explicitly pending.

## Planning correction

Generate feature-level Kiro briefs, requirements and designs from this backlog
before treating the foundation as the full implementation plan. The foundation
remains upstream infrastructure. A missing GPU unit blocks reproduction/testing
of GPU transitions, not inventory or design work for independent source features.
Source revision/API compatibility is a discovery gate, not grounds to omit the
original widgets, fonts, nvim-simple, coordinated themes or RDP helpers.

## Compositor approach correction

Owner explicitly selected configuration backporting to Ubuntu's native
Hyprland, prioritizing the original decorations they had ported forward.
The previous newer-compositor build investigation is superseded.

## RDP package correction

P21 is superseded by the owner's choice to use the upstream maintainer's GitHub
release archive. Do not port fork patches or rebuild RDP. Reuse only necessary
session/config behavior, after checking current upstream hooks and options.
The upstream README's0.54+ support statement requires verification against the
chosen Ubuntu0.53.3 desktop and must not be ignored.

## Owner-directed deferred work

Craft suite installer and LibreOffice (with language packs, UI layer and Carlito)
are moved to [backlog.md](backlog.md); current application port only inventories
these entries and does not install/configure them.

## Generated port specifications

| Feature | Executable tasks |
| --- | --- |
| [laptop-resource-policy](../.kiro/specs/laptop-resource-policy/tasks.md) | 11 |
| [rootless-containers](../.kiro/specs/rootless-containers/tasks.md) | 11 |
| [desktop-fonts](../.kiro/specs/desktop-fonts/tasks.md) | 8 |
| [application-suite](../.kiro/specs/application-suite/tasks.md) | 7 |
| [shell-user-tools](../.kiro/specs/shell-user-tools/tasks.md) | 20 |
| [coordinated-themes](../.kiro/specs/coordinated-themes/tasks.md) | 18 |
| [hyprland-desktop](../.kiro/specs/hyprland-desktop/tasks.md) | 27 |
| [hyprland-rdp](../.kiro/specs/hyprland-rdp/tasks.md) | 14 |

[Independent cross-spec review](../.kiro/specs/cross-spec-review.md): PASS.
