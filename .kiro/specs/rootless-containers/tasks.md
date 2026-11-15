# Implementation Plan

All executable work units target 1–3 hours. Checkboxes remain unchecked: these are planned implementation tasks. Foundation's implemented local-context/PackageGuard contract is an external prerequisite to task 1; resolve its pending approval through its owner, not by changing it here. The optional local entry point avoids shared root-deploy edits. Parallel markers are omitted because configuration, receipts and account state require ordered writes.

- [ ] 1. Establish feature inputs and read-only local preflight
  - Add the optional feature entry point, exact reviewed manifest, standard-library unittest fixture harness and typed preflight facts using the foundation's actual implemented import locations.
  - Validate resolute amd64, desktop identity, user bus, namespaces/AppArmor, local storage, cgroup/controller readiness and helper dependencies without global policy changes.
  - Detect existing Docker commands/packages/contexts, provider/environment overrides, foreign registry fragments and existing Podman data before planning changes.
  - Done: inventory and preview scaffolding return observed state, actionable conflicts and explicitly pending package/identity plans without writes, pulls or container execution; invalid contexts return nonzero. Complete preview acceptance follows tasks 2 and 4.
  - _Boundary: ContainerPreflight, ContainerDeploy integration_
  - _Requirements: 1.1, 1.4, 2.1, 2.3, 3.1, 4.4_

- [ ] 2. Integrate guarded native package resolution
  - Review native resolute packages and dependencies, rejecting transition installers and resolving no-recommends networking/identity/user-bus prerequisites explicitly.
  - Use only exact foundation PackageRequest, validate_request, inspect_plan and install_packages; no artifact source variant or duplicate guard.
  - Add fixtures for proposed removals, prohibited dependencies, unknown candidates and package failure after partial progress.
  - Done: permitted simulated plans install through foundation only, while prohibited/removal plans stop before feature state changes and report completed steps.
  - _Boundary: ContainerDeploy and PackageGuard integration_
  - _Depends: 1_
  - _Requirements: 1.1, 1.2, 1.4, 2.1_

- [ ] 3. Implement state receipts and non-destructive restoration primitives
  - Capture original path types/hashes/modes/owners and lifecycle states in user-only receipts before mutations; retain protected backups.
  - Restore only owned matching state, refusing post-apply user edits and retaining packages, runtime data, credentials and used identity allocations.
  - Add restore-conflict and partial-failure fixtures before later tasks consume these primitives.
  - Done: a temporary fixture tree restores precisely and a changed foreign path remains untouched with a conflict result.
  - _Boundary: ContainerRestore_
  - _Requirements: 1.3, 1.4, 5.3_

- [ ] 4. Plan and apply subordinate identity prerequisites safely
  - Preserve adequate existing ranges; allocate collision-free 65536-ID intervals only for missing mappings when no existing store/process needs migration.
  - Revalidate all account/range facts under account-management locks; reject malformed/overlapping ranges, races and migration requirements.
  - Add allocation, existing-range preservation, collision and retry failure fixtures.
  - Integrate the identity plan with task 2 package planning and the preview framework before enabling apply.
  - Done: complete preview reports resolved packages, intended identity allocations, files and lifecycle actions without mutations; repeated fixture application preserves existing mappings, avoids duplicates and leaves other accounts/container ownership unchanged.
  - _Boundary: ContainerConfig_
  - _Depends: 1, 2, 3_
  - _Requirements: 1.3, 2.1, 2.2, 2.3, 5.3_

- [ ] 5. Apply source-compatible command and registry configuration
  - Install owned configuration fragments and absent-or-owned docker-compose link, selecting the absolute native provider and validating installed-version configuration support.
  - Apply docker.io/permissive short-name policy only when compatible with existing effective policy; preserve credential stores and report conflicts.
  - Add compatibility/registry/provider-override/foreign-link fixtures and repeat-apply checks with receipts.
  - Done: four command forms identify Podman/podman-compose, effective provider and registry disposition are reported, and conflicting local tools/policies are unchanged.
  - _Boundary: ContainerConfig_
  - _Depends: 2, 3, 4_
  - _Requirements: 1.3, 3.1, 3.2, 3.4_

- [ ] 6. Configure and verify user lifecycle and resource disposition
  - Enable and start the user socket independently through the desktop user's real bus; preserve masked/foreign state with a diagnostic failure.
  - Record prior linger then configure login-independent user manager availability; inspect user-only socket path/permissions without enabling a rootful or TCP API.
  - Report source weight 200 and current placement/controller/effective weights; default to preserving scheduling, permitting explicit adoption only with proven correct scope.
  - Done: fixture and user-session checks distinguish enabled-but-inactive, inaccessible bus and undelegated controller states; restoration returns prior lifecycle values and no desktop/global slice policy changes occur.
  - _Boundary: ContainerLifecycle_
  - _Depends: 2, 3, 5_
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 5.3_

- [ ] 7. Implement the dedicated pinned terminal UI artifact route
  - Use the exact source URL/digest/version and dedicated separately reviewed feature-artifact contract; foundation PackageRequest remains Ubuntu-only.
  - Add unprivileged HTTPS staging, checksum-first validation, bounded safe extraction, unique executable/ELF/dependency/version checks, atomic owned-path install and content-aware idempotence.
  - Reject bad digest, traversal/links, oversized or ambiguous executable, wrong architecture, unavailable pin and foreign existing binary with fixture tests.
  - Done: valid fixture installation records provenance/content, repeat apply is unchanged, and failures preserve an existing executable and report unresolved TUI without fallback installers.
  - _Boundary: PodmanTuiArtifact_
  - _Depends: 2, 3, 6_
  - _Requirements: 1.3, 1.4, 5.1, 5.2_

- [ ] 8. Integrate bounded rootless acceptance paths
- [ ] 8.1 Verify isolated rootless runtime and storage
  - Implement read-only result reporting plus explicitly selected smoke mode with approved digest-pinned images, unique labels, temporary workspace and tightly scoped cleanup.
  - Verify rootless identity, DNS/outbound network and persistent test volume; capture failures while preserving all pre-existing resources.
  - Done: runtime smoke reports actual results and cleanup targets only the current run's recorded resources, with network failures preventing full success.
  - _Boundary: ContainerAcceptance integration_
  - _Depends: 4, 5, 6, 7_
  - _Requirements: 2.4, 5.4_

- [ ] 8.2 Verify compatibility commands and Compose workloads
  - Add the two-service Compose acceptance fixture using the existing isolated smoke infrastructure and unique project names.
  - Verify all four command forms identify the intended provider; test peer DNS and retained test data across a scoped project restart.
  - Done: Compose results demonstrate service discovery and persistence, cleanup preserves existing volumes/projects, and unsupported provider behavior returns an explicit failure.
  - _Boundary: ContainerAcceptance integration_
  - _Depends: 8.1_
  - _Requirements: 3.2, 3.3, 5.4_

- [ ] 8.3 Verify terminal UI against the rootless API
  - Connect the pinned podman-tui executable to the desktop user's Unix socket and confirm it lists the acceptance workload.
  - Check version, endpoint/permissions and failure reporting without changing credentials or enabling a privileged API.
  - Done: actual API/TUI evidence is recorded, or a pending/failure reason prevents full feature success; there is no fallback installer or daemon.
  - _Boundary: ContainerAcceptance integration_
  - _Depends: 7, 8.2_
  - _Requirements: 4.1, 5.1, 5.4_

- [ ] 9. Verify repeatability, restoration and lifecycle acceptance together
  - Run fixture contracts and local dry preview, then the explicit acceptance path only when foundation and host prerequisites are ready; compare owned files, identities and preserved runtime data across repeat application.
  - Exercise restoration against a disposable fixture and the feature's own test state, confirming original socket/linger settings and retained identity/data contracts.
  - Provide explicit pending check results for logout/relogin and reboot until those lifecycle checks are observed in the owner's environment; no fabricated runtime pass.
  - Done: the final result records actual checks/exit codes and unresolved conditions, with full feature success withheld until mandatory runtime/TUI/lifecycle checks pass.
  - _Boundary: ContainerAcceptance and ContainerRestore integration_
  - _Depends: 8.3_
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4_
