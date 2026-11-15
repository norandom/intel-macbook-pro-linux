# Requirements Document

## Introduction

The owner has a fresh Ubuntu KDE T2 Mac installation and wants the actual
source desktop from `norandom/hyperland-forky-worker-vm` revision
`a1c09ec3f02a98b7c6a4641f907108a2ad080993` available as a separate native-GPU
Hyprland session. No local feature implementation exists. The owner selected native Ubuntu Hyprland0.53.3/hyprbars0.53 and backporting
the newer source configuration, with original decorations the first priority.
This feature ports P14–P18 while preserving the owner's boot, encrypted storage and hardware setup.

## Boundary Context

In scope: compositor/plugin compatibility, session lifecycle, source window
behavior, complete Waybar, launchers, notifications, clipboard and desktop
helpers. Fonts and applications supply their published capabilities. Coordinated
themes owns terminal configuration, palettes, `hypr-term` and `hypr-termtheme`;
RDP owns remote transport/services. Battery and Bluetooth status widgets are
candidate additions requiring separate scope approval, not source features.

Out of scope: KDE removal or Plasma inside Hyprland, login-manager/default
changes, autologin, Snap/Flatpak, source VM rendering/device workarounds,
RDP units, GPU-policy reproduction and any protected boot/storage mutation.

## Requirements

### Requirement 1: Compatible and permitted desktop delivery
**Objective:** As the laptop owner, I want verified compatible desktop components, so that the source behavior works without destabilizing my installation.

#### Acceptance Criteria
1. The Desktop Port shall record an immutable source provenance and an explicit reused, adapted, delegated or excluded disposition for each source desktop asset and helper.
2. Before publishing a selectable session, the Desktop Port shall establish a compatible compositor, configuration and titlebar-plugin version/API combination using the native Ubuntu baseline and a verified backport of newer source configuration and helper behavior.
3. If a required native package, backported feature API or permitted installation route is unresolved, the Desktop Port shall report the exact blocker and leave session activation incomplete.
4. When preview is requested, the Desktop Port shall report package/build/file changes and unresolved prerequisites without downloads, file writes or service changes.
5. The Desktop Port shall reject Snap/Flatpak routes and dependency transitions, including package wrappers that install either runtime.

### Requirement 2: Preserve the T2 installation and fallback
**Objective:** As the laptop owner, I want a separate desktop that preserves my working host, so that I can continue using the laptop and KDE fallback.

#### Acceptance Criteria
1. The Desktop Port shall leave cryptsetup/LUKS/LVM, fstab/crypttab, swap/resume, kernels/modules/headers, bootloader and initramfs configuration/artifacts unchanged, including indirect package hooks or rollback actions.
2. Before any package transaction, the Desktop Port shall reject protected installs, upgrades, removals, replacements or maintainer-script/trigger effects; unknown hook effects shall block that transaction.
3. The Desktop Port shall preserve T2 firmware/support services, touch bar, keyboard/trackpad, camera, Wi-Fi/Bluetooth and existing GPU power configuration.
4. The Desktop Port shall preserve AppleT2 ALSA UCM, PipeWire, WirePlumber and local speaker/microphone/Bluetooth audio routing.
5. The Desktop Port shall retain KDE installed and dormant as a fallback and preserve SDDM authentication, configuration and default-session behavior.
6. If existing custom GPU-unit evidence is unavailable, the Desktop Port shall report reproduction and hardware-transition acceptance as pending without inventing a replacement GPU mechanism.

### Requirement 3: Independent session lifecycle
**Objective:** As the laptop owner, I want a full selectable Hyprland session, so that I can use the source desktop without Plasma running.

#### Acceptance Criteria
1. When the owner explicitly selects Hyprland at SDDM, the Desktop Port shall start the full desktop with native GPU rendering, applications, notifications and supported portals without starting Plasma.
2. When Hyprland starts or exits, the Desktop Port shall start or stop its session-owned processes and clear stale session environment without interfering with KDE sessions.
3. When configuration reloads, the Desktop Port shall avoid duplicate services, timers, callbacks and titlebar buttons and shall preserve application processes launched from the bar.
4. When the owner requests logout, the Desktop Port shall end only the active Hyprland session and return to the existing login flow.
5. The Desktop Port shall provide explicit lock and power-menu actions without imposing the source VM's RDP-presence initial lock or autologin behavior.
6. When a new Xwayland instance becomes available, the Desktop Port shall invoke the font spec's bounded font-registration helper and report failed registration distinctly from pending display availability.

### Requirement 4: Windows, layouts and decorations
**Objective:** As a desktop user, I want the source window-management features, so that the port retains the intended desktop interaction.

#### Acceptance Criteria
1. When a layout is selected, the Desktop Port shall support dynamic floating with per-application geometry memory, golden-h, golden-v and golden-spiral, including existing-window transitions and a visible selected mode.
2. When a floating window is dragged to a screen edge or corner, the Desktop Port shall support half-screen, maximized and quarter-screen snapping while keeping titlebars reachable outside reserved bar space.
3. When display size or scale changes, the Desktop Port shall keep floating-window geometry usable on available physical monitors without disabling laptop input or outputs.
4. When a decoration style is selected, the Desktop Port shall support persistent mac and win311 titlebars, source hostcolor-derived borders and the style's close, maximize/minimize, glass and pin actions.
5. When glass, pin or shadows are changed, the Desktop Port shall apply the selected window/desktop effect and expose its actual state without changing unrelated windows' preferences.
6. When a window is minimized, the Desktop Port shall allow restoring it through the taskbar or minimized-window command.
7. When the owner uses the source key/mouse controls, the Desktop Port shall provide launch, focus, move, resize, close, fullscreen, layout and one-shot Super actions with visible armed-submap feedback and cancellation.

### Requirement 5: Full source bar and launchers
**Objective:** As a desktop user, I want the original widgets and application menu, so that the port is a complete usable desktop.

#### Acceptance Criteria
1. The Desktop Port shall provide the source Apps, files, terminal, browser, layout, taskbar, clock, quota, CPU, memory, network, audio drawer/slider, tray, submap, clipboard, nightmode, terminal-theme, keyboard and power modules.
2. Where graph mode is selected, the Desktop Port shall provide source CPU/memory/network sparklines; otherwise it shall provide numeric statistics and preserve the source refresh/interaction behavior.
3. When Apps or desktop-context-menu is invoked, the Desktop Port shall provide categorized applications, recent entries, Run/search, icons and keyboard navigation with Escape/outside-click dismissal.
4. If an application or optional quota credential is unavailable, the Desktop Port shall display unavailable/unknown/stale status and an actionable reason without falsely reporting installation or exposing secrets.
5. When an application is launched from the bar/menu, the Desktop Port shall honor desktop-entry launch semantics and preserve argument boundaries, and the application shall survive a bar reload.
6. When volume/mute/slider controls are used, the Desktop Port shall control the current PipeWire-compatible audio route without requiring plasma-pa or starting Plasma.
7. When quota is requested, the Desktop Port shall preserve source provider distinctions, bounded queries and stale-cache reporting without collecting or migrating account credentials.
8. When visual configuration is provisioned, the Desktop Port shall retain source Waybar/Fuzzel/Mako/GTK styling, power artwork and an initial Xfe seed while preserving later user edits.

### Requirement 6: Clipboard, notifications and night filters
**Objective:** As a desktop user, I want the source utility behavior, so that common native and X11 workflows remain functional.

#### Acceptance Criteria
1. When clipboard history is enabled, the Desktop Port shall retain at most 200 entries in the user's runtime storage, exclude sensitive and focused-password-manager copies, and support picker/status/manual wipe and the source 01:00 wipe schedule.
2. When the clipboard contains only legacy X11 STRING text, the Desktop Port shall bridge Latin-1 to UTF-8 without replacing an already valid UTF-8/text selection or creating a conversion loop.
3. When the session ends, the Desktop Port shall stop clipboard watchers and discard its history without deleting another session's unrelated data.
4. When a notification is sent in Hyprland, the Desktop Port shall display it with the source notification styling without conflicting notification daemons.
5. When nightmode is selected, the Desktop Port shall support off, green and dark source shaders, persist the choice and reapply it after reload, with accurate bar feedback.

### Requirement 7: Input, integration and recovery
**Objective:** As the laptop owner, I want reliable integration and reversible provisioning, so that source adaptations remain reviewable and recoverable.

#### Acceptance Criteria
1. When keyboard layout is switched, the Desktop Port shall support source US/DE choice and persisted selection preserving the source Super/Command/Option mapping, including German Mac Option+L producing @, without changing console, LUKS or initramfs keyboard behavior.
2. When physical monitors or input devices are discovered, the Desktop Port shall use native available devices and preserve usable local input/output without VM names, virtual-output assumptions or forced software rendering.
3. When terminal/theme controls are invoked, the Desktop Port shall use the theme feature's executable/state contract without writing terminal configs or palettes.
4. When RDP integration queries the desktop, the Desktop Port shall expose an explicit selected-session environment/lifecycle contract without managing RDP units, remote audio routing or remote input transitions.
5. When provisioning repeats or an owned file changes, the Desktop Port shall report changed/unchanged/failed/pending results, preserve unrelated configuration and retain backups for explicitly adopted files.
6. When restoration is requested, the Desktop Port shall restore only owned desktop changes, detect user-edit conflicts and leave protected host state and shared packages untouched.
7. When acceptance is reported, the Desktop Port shall distinguish document/static checks from real session and T2 hardware checks, including speaker/mic, camera, touch bar, input, Wi-Fi/Bluetooth and suspend/resume.
