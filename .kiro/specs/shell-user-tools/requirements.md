# Requirements Document

## Introduction
The owner of a fresh Ubuntu KDE T2 Mac wants the source repository's Bash, Neovim and user development tools, which are absent from the current uv/pyinfra/nvm foundation. This specification ports P10–P13 from revision `a1c09ec3f02a98b7c6a4641f907108a2ad080993`, with explicit compatibility gates and restoration.

## Boundary Context
In scope: grml-inspired Bash/readline/history, pinned nvim-simple and plugins, user Node/Python/agent tools, completions and optional cloud mounts, cache helper and Quarto environments. Tools remain usable in KDE and the planned standalone Hyprland session. Resource policy supplies turbo aliases; application-suite supplies native executables. Coordinated themes supplies terminal configurations and Neovim desktop-theme integration. Foundation supplies uv/nvm and guarded native installation. No source credentials, Snap/Flatpak, automatic destructive cleanup, source snitch removal, KDE removal or T2 hardware changes are included.

## Requirements

### Requirement 1: Interactive shell experience
**Objective:** As the desktop owner, I want the source Bash conveniences without losing my existing shell configuration.

#### Acceptance Criteria
1. When an interactive Bash starts, the Shell Tools shall provide the source directory stack, aliases, helper functions and user/host/directory/Git prompt with failed-command status.
2. When the owner searches history or completes a command, the Shell Tools shall provide prefix Up/Down history search, case-insensitive completion and source large timestamped shared history behavior.
3. When an existing shell configuration is extended or sourced repeatedly, the Shell Tools shall retain unrelated settings and prompt hooks without duplicate managed hooks or PATH entries.
4. While a shell is noninteractive, the Shell Tools shall avoid interactive prompts, history manipulation and desktop command execution.
5. Where the resource turbo fragment is readable, the Shell Tools shall expose its aliases without changing turbo state during shell startup.
6. If a desktop keyboard helper is unavailable or the active session is KDE, the Shell Tools shall preserve ordinary keyboard configuration commands rather than redirect them to Hyprland.

### Requirement 2: Source editor experience
**Objective:** As the owner, I want the source simple editor with reliable installation and recoverable configuration.

#### Acceptance Criteria
1. When the editor is provisioned, the Shell Tools shall install the selected pinned nvim-simple configuration and its menu, status-line, file explorer and icon plugins.
2. When the editor opens, the Shell Tools shall provide the source CUA editing keys, menu access, explorer, terminal tabs and Berg light/dark toggle.
3. If an existing editor configuration or data conflicts with installation, the Shell Tools shall preserve it in a unique recoverable backup before replacement and shall retain unrelated editor data.
4. If a plugin download, compatibility check or headless initialization fails, the Shell Tools shall report the editor as incomplete without replacing a working configuration or recording success.
5. Where coordinated themes is absent, the Shell Tools shall retain standalone Berg behavior without requiring a desktop session or special font.

### Requirement 3: User developer and agent tools
**Objective:** As the owner, I want source development commands in isolated user environments.

#### Acceptance Criteria
1. When selected developer tools are provisioned, the Shell Tools shall make pnpm, Copilot CLI, Codex CLI and ccusage available under the foundation-selected user Node runtime without sudo or a conflicting global prefix.
2. When selected Python notebook tooling is provisioned, the Shell Tools shall provide euporie and an executable Python kernel in isolated user environments without changing system Python or the repository's locked environment.
3. When selected agent skill tooling is provisioned, the Shell Tools shall install the source pretty-mermaid skill from reviewed immutable inputs without overwriting unrelated skills or agent settings.
4. If selected package versions, dependency artifacts or runtime prerequisites are unverified, the Shell Tools shall report the affected tool as blocked rather than silently install a moving release.
5. When authentication is needed, the Shell Tools shall leave login to the owner and shall avoid copying source credentials or exporting account tokens on every shell startup.

### Requirement 4: Package-manager protection and command completion
**Objective:** As the owner, I want source package-manager protection and completions that respect the selected toolchain.

#### Acceptance Criteria
1. When Safe Chain is selected, the Shell Tools shall verify its pinned artifact and activate protection for supported source package-manager commands without replacing foundation runtime selection.
2. If protection setup fails, conflicts with existing wrappers, or resolves the wrong runtime, the Shell Tools shall report protection as unavailable without silently bypassing it for a requested protected installation.
3. When kubectl, helm, gh, ax or rc is available, the Shell Tools shall provide matching Bash completion and kubectl alias completion from that executable.
4. If a completion provider is absent or fails, the Shell Tools shall preserve unrelated completions and report the unavailable provider without publishing a partial completion file.
5. Where ax is selected, the Shell Tools shall install the source-pinned CLI using its reviewed Go toolchain without clearing shared Go caches.

### Requirement 5: Optional user services and client tools
**Objective:** As the owner, I want optional source capabilities with explicit prerequisites and no inherited VM roles.

#### Acceptance Criteria
1. Where cloud mounts are explicitly selected, the Shell Tools shall provide user mount units only for owner-configured remotes and safe empty mount locations, retaining existing mount data and credentials.
2. If a remote, FUSE support or user service manager is unavailable, the Shell Tools shall report the mount as pending without claiming it mounted or repeatedly restarting an invalid service.
3. Where cache maintenance is selected, the Shell Tools shall provide a report-only default and require explicit apply selection for bounded user cache deletion.
4. When the optional cache timer runs, the Shell Tools shall perform reporting only and shall avoid package removal, container-volume deletion, project deletion and protected tool/environment deletion.
5. Where Quarto Python or TinyTeX is explicitly selected, the Shell Tools shall validate the supplied Quarto prerequisite and reviewed dependencies before creating the corresponding user environment without inferring a client role from hostname.

### Requirement 6: Preservation and recoverability
**Objective:** As the owner, I want tools added without disrupting the fresh laptop baseline.

#### Acceptance Criteria
1. The Shell Tools shall preserve foundation's Node initialization, the prohibited-package policy, KDE fallback, login behavior and T2 kernel, boot, firmware, touch bar, input, audio, camera, networking and suspend support.
2. When native dependencies are requested, the Shell Tools shall reject prohibited packaging routes and package plans that remove packages or install, upgrade, replace, regenerate or reconfigure protected cryptsetup/LUKS/LVM, fstab/crypttab, swap/resume, kernel/modules/headers, bootloader or initramfs state, including maintainer scripts and triggers.
3. When a feature is applied again with unchanged inputs, the Shell Tools shall avoid duplicate startup changes, unnecessary downloads and replacement of unchanged owned files.
4. When restoration is requested, the Shell Tools shall restore captured owned files and unit states, report conflicting later edits and retain unrelated packages, user data and credentials.

### Requirement 7: Execution and evidence
**Objective:** As the owner, I want an optional, reviewable tool deployment with honest status.

#### Acceptance Criteria
1. When preview is requested, the Shell Tools shall show selected changes and prerequisite failures without downloads, package installation, user-file mutation or service activation.
2. When an operation fails or is blocked, the Shell Tools shall return a nonzero result for a required selected capability and distinguish installed, configured, authenticated, running, blocked and unselected states.
3. When validation is reported, the Shell Tools shall distinguish static checks and isolated tests from real KDE/Hyprland and physical T2 verification.
