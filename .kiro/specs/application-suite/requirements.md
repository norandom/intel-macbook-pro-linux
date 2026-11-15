# Requirements Document

## Introduction

Port the source repository's application inventory to the Ubuntu T2 laptop
without losing source features or bypassing the strict no Snap/Flatpak policy.
This includes native application binaries and release tools, while neighboring
specs own their feature configuration.

## Boundary Context

- In scope: complete disposition manifest, permitted installation routes,
  application binaries and minimal source application settings.
- Out of scope: deferred LibreOffice/Carlito and Craft suite installation/configuration; nvm/npm/uv user tools, nvim-simple configuration, container
  runtime/podman-tui, theme palettes, terminal profiles and compositor services.
- Adjacent expectations: foundation supplies local-user execution and package
  policy. Existing installed applications remain available; unspecified optional
  client apps require selection before installation, not implicit removal.

## Requirements

### Requirement 1: Complete source inventory
**Objective:** As the owner, I want every source app accounted for, so that the port cannot silently shrink to a few utilities.

#### Acceptance Criteria
1. The application port shall identify every application and release tool declared by the pinned source application task and its configured release/client maps.
2. The application port shall assign each source entry an owning feature and an explicit installation, delegated, optional, excluded, or unresolved disposition.
3. If an entry is unresolved, the application port shall report the missing selection, artifact or compatibility evidence.
4. The application port shall retain source provenance for each selected version or artifact.

### Requirement 2: Permitted installation routes
**Objective:** As the owner, I want native applications, so that the installation respects my package policy.

#### Acceptance Criteria
1. When installing selected native packages, the application port shall use the foundation's reviewed package-policy contract.
2. The application port shall reject Snap/snapd, Flatpak and transitional installers that delegate to them.
3. If a native artifact or vendor route is selected, the application port shall validate its provenance, integrity, architecture and runtime compatibility before installation.
4. If no permitted compatible route exists, the application port shall leave the entry unresolved without substituting a prohibited package system.

### Requirement 3: Application capability and integration
**Objective:** As the owner, I want the source's application capabilities available where selected, so that widgets and tools launch useful programs.

#### Acceptance Criteria
1. When a source application is selected and its route validated, the application port shall provide its expected executable and required runtime dependencies.
2. The application port shall report LibreOffice, its language support, tabbed UI and Carlito font as deferred backlog without installing or configuring them in the current port.
3. The application port shall retain the source Craft suite installer inventory as deferred backlog without installing or activating its applications in the current port.
4. When a downstream feature queries application availability, the application port shall distinguish verified executable availability from a merely planned installation.

### Requirement 4: Preserve user state
**Objective:** As the owner, I want additive installation, so that the port does not remove working applications or local settings.

#### Acceptance Criteria
1. The application port shall preserve unselected applications and user data rather than inherit source host-role purge behavior.
2. If a managed application-setting change conflicts with existing local configuration, the application port shall preserve a restorable prior state and report its change scope.
3. The application port shall leave application credentials and licenses outside committed configuration.
4. When provisioning is repeated against matching application state, the application port shall leave that state unchanged.

### Requirement 5: Reviewable and recoverable installation
**Objective:** As the owner, I want observable application changes, so that failed ports can be corrected without guessing.

#### Acceptance Criteria
1. When a preview is requested, the application port shall show selected changes and unresolved entries without installing packages or changing configuration.
2. If dependency resolution, integrity checks or installation fails, the application port shall report the affected application and return failure for selected required work.
3. The application port shall distinguish ready, installed, optional-unselected and blocked entries in its result report.
4. The application port shall preserve the existing login, GPU and T2 boot configuration.
