# Requirements Document

## Introduction
The laptop owner has a working Ubuntu KDE T2 Mac and uv/pyinfra baseline, but lacks the source rootless container experience. P07 ports Podman, Docker command compatibility, Compose and podman-tui while preserving existing runtime data and desktop behavior.

## Boundary Context
- In scope: rootless execution, prerequisite identity ranges, container tools/configuration, user API lifecycle, linger and evaluated scheduling.
- Out of scope: privileged Docker deployment, migration/deletion of existing runtime data, desktop/GPU/global resource policy, Snap/Flatpak.
- Adjacent expectations: foundation supplies guarded native package installation and local privilege handling; application-suite does not install podman-tui. No shared deploy entry point changes are included here.

## Requirements

### Requirement 1: Preserved host and permitted installation
**Objective:** As the owner, I want a repeatable preview and apply workflow that preserves my laptop.

#### Acceptance Criteria
1. When preview is requested, the container provisioning workflow shall report proposed packages, files, identity allocations and lifecycle changes without changing the host.
2. If a package route violates the no Snap/snapd or Flatpak policy or proposes removing existing packages, the workflow shall stop before installation and identify the conflict.
3. When provisioning is repeated, the workflow shall preserve existing containers, images, volumes, registry credentials and unrelated user configuration without duplicating managed state.
4. If a prerequisite or installation step fails, the workflow shall return a nonzero result identifying the failed step and any completed changes.

### Requirement 2: Rootless container execution
**Objective:** As the desktop user, I want containers with working networking and storage without a privileged daemon.

#### Acceptance Criteria
1. When rootless readiness is checked, the workflow shall verify the selected user's subordinate identity mappings, namespace support, local storage and unprivileged networking prerequisites.
2. If existing subordinate mappings are valid, the workflow shall retain their values; if mappings are absent, the workflow shall allocate nonoverlapping available ranges without altering other accounts.
3. If existing storage or identity mappings would require migration, the workflow shall stop and report the required intervention without resetting containers or remapping their data.
4. When the desktop user starts the acceptance container, the container environment shall execute it rootlessly with working name resolution, outbound networking and persistent test-volume access.

### Requirement 3: Docker commands and Compose
**Objective:** As the owner, I want the source command forms for ordinary local development workloads.

#### Acceptance Criteria
1. If an existing Docker installation, command, socket preference or Compose integration conflicts with compatibility setup, the workflow shall report the conflict and preserve the existing installation.
2. When compatibility setup succeeds, the container environment shall provide docker, docker compose, docker-compose and podman compose commands backed by the rootless Podman workflow.
3. When a uniquely named acceptance Compose project is started, the container environment shall run its services with name resolution and persistent test data and remove only its own test resources during cleanup.
4. When image-name policy is applied, the workflow shall report the source short-name behavior and the selected local disposition without silently replacing existing registry policy or credentials.

### Requirement 4: User lifecycle and scheduling
**Objective:** As the owner, I want container API tools and lifecycle behavior with an observable desktop impact.

#### Acceptance Criteria
1. When user lifecycle setup succeeds, the container environment shall expose a socket-activated API restricted to the desktop user without enabling a privileged container daemon or network API listener.
2. When login-independent lifecycle is configured, the workflow shall report the resulting linger and socket states and retain their prior values for restoration.
3. When container scheduling is configured, the workflow shall report the source CPU weight, local decision and effective container cgroup placement without changing desktop or global CPU policies.
4. If the user manager or required resource controller is unavailable, the workflow shall report that limitation without claiming lifecycle or scheduling acceptance.

### Requirement 5: Terminal UI and restoration
**Objective:** As the owner, I want the source terminal UI and a reliable recovery path.

#### Acceptance Criteria
1. When podman-tui is installed, the workflow shall use a reviewed native package or checksum-pinned upstream artifact and verify the installed executable's version and connection to the rootless user API.
2. If no reviewed compatible route or artifact verification is available, the workflow shall leave podman-tui unresolved and report the reason without falling back to a prohibited installer.
3. When restoration is requested, the workflow shall restore only feature-owned configuration and prior lifecycle settings while preserving runtime data, existing tools and identity mappings used by containers.
4. When acceptance results are reported, the workflow shall distinguish completed static checks, runtime checks and unresolved or manual checks, and shall not report full feature success while a mandatory check is pending.
