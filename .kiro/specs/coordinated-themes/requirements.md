# Requirements Document

## Introduction
The Ubuntu KDE T2 laptop owner lacks the original source terminal and coordinated application themes. Port P19–P20 from `norandom/hyperland-forky-worker-vm` revision `a1c09ec3f02a98b7c6a4641f907108a2ad080993`, retaining all five actual palettes and recoverable existing settings.

## Boundary Context
Include terminal configuration, palette assets/generators, terminal/theme commands, Terminator menu/tab styling, installed application theme targets and the Neovim theme bridge. Fonts supplies public families; shell supplies the standalone Neovim base; applications supplies installed executables. Desktop consumes theme commands/state and owns its Waybar module, compositor decoration/tint/shaders and session launch integration. KDE global appearance, shell startup, application installation and protected boot/storage/hardware changes are excluded.

## Requirements

### Requirement 1: Actual source palettes
**Objective:** As the owner, I want the original five palettes so the port retains the source appearance.

#### Acceptance Criteria
1. When themes are provisioned, the Theme Port shall provide cobalt, navy, fixedsys, cream and petrol using the pinned source colors, cursor colors, syntax colors and tab styling.
2. When a profile is selected, the Theme Port shall retain its source font family/size selection and report any unavailable private family with the effective public fallback.
3. When source assets are prepared, the Theme Port shall account for every source palette target and generator with an explicit reused, adapted, optional or incompatible disposition.

### Requirement 2: Coordinated selection and launch
**Objective:** As the owner, I want one selection to coordinate my terminal and supported installed applications.

#### Acceptance Criteria
1. When the owner selects a profile or cycles forward/backward, the Theme Port shall retain the source order, persist the selected profile and apply the matching themes to eligible selected applications.
2. When current selection is reapplied, the Theme Port shall repair eligible managed theme settings without cycling or needlessly rewriting unchanged files.
3. When a terminal is launched through the source helper, the Theme Port shall use the selected profile, preserve each supplied argument and return the terminal process result.
4. If a profile argument is invalid, the Theme Port shall report usage failure and leave current selection and application settings unchanged.
5. While no compositor or desktop bar is available, the Theme Port shall support theme selection and launch without treating their absence as failure.

### Requirement 3: Application behavior
**Objective:** As the owner, I want the supported source applications coordinated without unwanted installations or damage to preferences.

#### Acceptance Criteria
1. Where Terminator is selected and installed, the Theme Port shall provide the five profiles, theme context menu, source slim tab styling and current-profile selection for existing and new windows.
2. Where Ghostty, foot, btop, Claude Code, Sublime Text, VS Code or Positron is selected and compatible, the Theme Port shall apply its source palette and applicable font settings with explicit live-reload or next-launch status.
3. Where xfce4-terminal is selected and compatible, the Theme Port shall retain its source cobalt settings and unsafe-paste review behavior without claiming source five-profile switching for that application.
4. Where the shell editor base is available, the Theme Port shall select Berg light on the next Neovim start for cream and Berg dark for other profiles while retaining the manual toggle.
5. Where a compatible installed Chromium browser and explicit policy selection are available, the Theme Port shall offer the source constant cream browser frame independently of palette cycling.
6. If an application is absent, unsupported or unselected, the Theme Port shall preserve its configuration, report its disposition and avoid installing it.

### Requirement 4: Preservation and failure handling
**Objective:** As the owner, I want recoverable coordinated changes so existing working preferences remain usable.

#### Acceptance Criteria
1. When application settings are updated, the Theme Port shall preserve unrelated settings, comments and formatting in supported commented configuration formats.
2. If settings are malformed, ambiguous or concurrently changed, the Theme Port shall leave those settings untouched and report the target as unapplied.
3. If a required eligible target fails before selection publication, the Theme Port shall preserve the previous committed selection and restore its own partially published file changes, reporting any restoration conflict.
4. When scoped restoration is requested, the Theme Port shall restore only its recorded changes and preserve later user edits and other features' configuration.

### Requirement 5: Reproducible safe execution and evidence
**Objective:** As the operator, I want bounded repeatable provisioning with honest validation status.

#### Acceptance Criteria
1. When preview is requested, the Theme Port shall report changes and prerequisites without changing packages, application settings, selection, caches or live processes.
2. When dependencies are required, the Theme Port shall use the existing foundation execution/package-policy contract and reject Snap/snapd, Flatpak and protected boot/storage or T2 hardware mutations including indirect hooks.
3. When provisioning or switching completes, the Theme Port shall distinguish applied, unchanged, skipped, incompatible, failed and pending-live targets without exposing private application settings.
4. When validation is reported, the Theme Port shall distinguish source/static/fixture evidence from actual application and physical-session acceptance and leave unavailable runtime checks pending.
