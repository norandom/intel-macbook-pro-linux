# Requirements Document

## Introduction
The owner of a physical 64 GB Ubuntu KDE T2 Mac has an existing uv/pyinfra/nvm foundation but lacks the source resource-management features. Port backlog P01–P06 from source revision `a1c09ec3f02a98b7c6a4641f907108a2ad080993`: turbo controls, memory safeguards, justified development tuning and laptop service policy.

## Boundary Context
- **In scope:** boot turbo default, exact requested shell controls, compressed swap, early memory-pressure intervention, diagnostic-storage limits, individually assessed tuning and Avahi suppression.
- **Out of scope:** GPU changes, VM boot/kernel profile, serial console, root SSH/password policy, module blacklists, automatic root remount/commit=60, QEMU agent, snitchd, Snap/Flatpak, desktop removal and autologin.
- **Adjacent expectations:** foundation supplies permitted package execution; shell-user-tools loads the resource-owned alias fragment without disturbing nvm. Disk swap and existing resume/hibernation configuration are preserved; creating a new hibernation configuration or guaranteeing hibernation capacity is outside this feature. The fresh T2 installation keeps package-owned audio configuration; protecting an available KDE session does not require starting Plasma inside Hyprland.

## Requirements

### Requirement 1: Turbo control
**Objective:** As the laptop owner, I want turbo disabled at boot and explicit interactive controls, so that I can choose runtime CPU behavior.

#### Acceptance Criteria
1. **1.1** When the laptop boots with the supported turbo-control interface available, the Resource Policy shall set and verify the requested disabled turbo default.
2. **1.2** When the owner invokes `turbo-on`, `turbo-off` or `turbo-status` after sourcing the provided shell fragment, the Resource Policy shall expose the exact alias behavior recorded in the owner's intake and report the underlying state.
3. **1.3** If the turbo-control interface is unavailable or a write fails, the Resource Policy shall report the unsupported interface or failed operation without reporting successful activation.
4. **1.4** When installing turbo controls, the Resource Policy shall preserve existing shell customization and nvm initialization and provide a separate fragment for the shell feature to load.

### Requirement 2: Compressed swap without losing disk swap
**Objective:** As the laptop owner, I want additional compressed swap suitable for this laptop, so that memory pressure can be handled without replacing existing swap or resume settings.

#### Acceptance Criteria
1. **2.1** When preparing compressed swap, the Resource Policy shall identify existing swap providers, priorities and resume configuration and report its selected size, compression algorithm and priority with a laptop-specific rationale.
2. **2.2** While compressed swap is configured, the Resource Policy shall retain existing disk swap, its priority and all existing resume/hibernation configuration and shall give the managed compressed swap a higher priority than disk swap.
3. **2.3** When compressed-swap configuration changes, the Resource Policy shall stage a safe activation path without automatically stopping or recreating active swap devices.
4. **2.4** If an existing compressed-swap manager, unavailable algorithm or incompatible priority prevents the selected policy, the Resource Policy shall report the conflict and leave the conflicting swap configuration unchanged.

### Requirement 3: Memory-pressure intervention
**Objective:** As the laptop owner, I want memory-pressure safeguards that account for both desktops, so that intervention does not preferentially destroy the session.

#### Acceptance Criteria
1. **3.1** When preparing early memory-pressure intervention, the Resource Policy shall report the effective thresholds, existing OOM managers and process-selection policy before enabling the new policy.
2. **3.2** While early memory-pressure intervention is active, the Resource Policy shall deprioritize killing the observed KDE/Plasma/KWin and Hyprland desktop/session stack, accounting for the process-name representation used by the installed manager.
3. **3.3** When evaluating source browser-kill preferences, the Resource Policy shall record whether each preference is adopted or rejected and expose the resulting effective process policy.
4. **3.4** If an existing OOM policy conflicts with safe activation of the new intervention policy, the Resource Policy shall report the conflict without automatically disabling the existing policy or enabling competing killers.

### Requirement 4: Diagnostic storage bounds
**Objective:** As the laptop owner, I want bounded journal and crash storage, so that diagnostics remain available without uncontrolled disk use.

#### Acceptance Criteria
1. **4.1** When applying journal policy, the Resource Policy shall establish persistent and runtime limits of 500M and 100M respectively and report the merged effective settings.
2. **4.2** When applying crash-storage policy, the Resource Policy shall identify the active crash handler and apply 500M maximum retained storage and 1G minimum free-space settings only when the handler supports those settings.
3. **4.3** If another crash handler is active, the Resource Policy shall preserve it and report that the source crash-storage limits are inapplicable rather than claim that they are enforced.

### Requirement 5: Justified development tuning
**Objective:** As the laptop owner, I want each source tuning assessed for a physical laptop, so that source defaults do not silently become laptop policy.

#### Acceptance Criteria
1. **5.1** When evaluating source tuning, the Resource Policy shall record an adopt or reject disposition, host-specific rationale, effective-state check and restoration action for each reclaim, dirty-writeback, network, file/inotify limit, temporary-filesystem, access-time and watchdog setting.
2. **5.2** When adopting tuning, the Resource Policy shall preserve higher existing development limits and report unsupported settings or conflicting local overrides before changing them.
3. **5.3** While applying resource policy, the Resource Policy shall preserve existing T2 boot arguments, GPU settings, hardware modules, root SSH policy and filesystem durability/mount policy.

### Requirement 6: Laptop service policy
**Objective:** As the laptop owner, I want unwanted discovery disabled while laptop capabilities remain usable, so that the VM disable list does not impair the laptop.

#### Acceptance Criteria
1. **6.1** When applying service policy, the Resource Policy shall stop and prevent activation of Avahi through its installed service, socket and D-Bus activation paths and report the effective result.
2. **6.2** While service policy is applied, the Resource Policy shall preserve Bluetooth, existing laptop power management, CUPS printing capability, apple-t2-audio-config ALSA UCM profiles, PipeWire/WirePlumber, Bluetooth audio and unrelated modem/hardware services.
3. **6.3** When reporting printing capability with Avahi disabled, the Resource Policy shall explain that automatic mDNS/DNS-SD discovery is unavailable and retain the ability to configure printing through a direct address without inventing a printer configuration.
4. **6.4** While applying service policy, the Resource Policy shall exclude QEMU-agent and snitchd installation, activation and firewall changes.

### Requirement 7: Reviewable and reversible execution
**Objective:** As the laptop owner, I want inspectable changes and restoration, so that resource policy can be retried or removed without erasing working configuration.

#### Acceptance Criteria
1. **7.1** Before changing managed resources, the Resource Policy shall expose planned operations and capture the prior contents, effective values and service/mask states needed to restore those resources.
2. **7.2** When resource policy is run again with unchanged inputs, the Resource Policy shall avoid duplicate configuration and unnecessary service restarts or swap transitions.
3. **7.3** When verifying or restoring policy, the Resource Policy shall distinguish persisted configuration, effective runtime state, deferred activation and failed or unavailable checks and shall restore only its own changes.
4. **7.4** While resolving resource-policy dependencies, the Resource Policy shall use the foundation's permitted native package path and preserve the prohibition on Snap/snapd and Flatpak, including indirect installation routes.
