# Implementation Plan

This is the upstream foundation only. The source-derived feature port backlog
is [source-port-plan.md](../../../docs/source-port-plan.md), with 23 port work
items. This foundation plan does not deliver those features by itself.

Scope: local-system-foundation only. Each executable item is a bounded 1–3 hour
unit. GPU configuration and the broader desktop port remain outside this plan.
Tests use fixtures and disposable targets; this plan does not schedule host deployment.

- [ ] 1. Establish local execution and validation prerequisites
- [x] 1.1 Validate desktop-user execution before any mutation
  - Establish the shared management namespace and local-context checks described in the design.
  - Reject root execution, non-local inventory, and unsupported operating systems before writes.
  - Add fixture-based checks using the standard-library test runner, so no unapproved dependency or package manager is needed.
  - Done when valid desktop-user context passes and each invalid context exits with a specific failure and no writes.
  - _Boundary: Preflight_
  - _Requirements: 2.2, 2.4, 5.1, 5.2, 5.3, 5.5, 5.6_

- [ ] 1.2 Preserve locked, isolated bootstrap behavior
  - Validate Python/curl prerequisites and report missing tools without attempting prohibited fallback installation.
  - Preserve existing uv or install the pinned bootstrap version, clean temporary files on failure, and sync only against the committed lock.
  - Verify a valid lock creates the project-local environment and a stale declaration fails without changing the lock or global Python.
  - Done when bootstrap success/failure cases pass in temporary projects and failed downloads return nonzero status.
  - _Boundary: Bootstrap_
  - _Requirements: 1.1, 1.2, 1.3, 2.4_

- [ ] 2. Implement strict system-package policy
- [ ] 2.1 Validate requested and resolved package plans
  - Implement the validated request/plan contracts and native-Ubuntu source restriction from the design.
  - Reject direct or architecture-qualified prohibited packages, option-like arguments, unreviewed manifests, proposed removals, and dependency failures.
  - Inspect apt simulations with fixed locale and fail closed on unrecognized output; retain resolved versions and reject protected boot/storage/kernel transactions, including maintainer-script or trigger regeneration paths. Unknown hook behavior blocks the affected plan.
  - Cover direct/transitive prohibitions, transition-package fixtures, unknown sources and malformed output with meaningful unit fixtures.
  - Done when permitted native plans pass and every prohibited, unresolved, or unrecognized plan fails before package writes.
  - _Boundary: PackageGuard_
  - _Depends: 1.1_
  - _Requirements: 2.1, 2.4, 4.1, 4.3, 4.4, 4.5, 5.6_

- [ ] 2.2 Maintain and validate effective negative apt pins
  - Add the owned snapd/Flatpak policy while preserving the user's existing snapd block byte-for-byte.
  - Back up an existing owned policy file before replacement and support restoration limited to that owned file; never remove or rewrite the user's snapd block.
  - Detect installed prohibited runtimes and effective-policy conflicts, reporting remediation pending without purging applications or user data.
  - Implement read-only preview with the intended temporary policy overlay; candidate absence alone must not count as verified pinning.
  - Cover conflicting administrator pins and available prohibited versions in disposable-policy fixtures.
  - Done when effective prohibition is verified, conflicting/preinstalled states block package work, and preview leaves host apt configuration unchanged.
  - _Boundary: PackagePolicy_
  - _Depends: 1.1_
  - _Requirements: 2.1, 2.4, 2.5, 4.2, 4.5_

- [ ] 2.3 Integrate package-plan validation with guarded installation
  - Combine request validation, effective policy and plan inspection into the sole managed apt-install entry point.
  - Revalidate after indexes/policy change and immediately before applying the same package arguments used for simulation.
  - Preserve no-recommends behavior, reject removals and policy bypass options, and propagate apt/authentication failures.
  - Verify that satisfied packages cause no package changes on a repeat run.
  - Done when disposable integration checks show policy gates precede every managed package installation and failures remain nonzero.
  - _Boundary: Integration — PackageGuard, PackagePolicy_
  - _Depends: 2.1, 2.2_
  - _Requirements: 2.1, 2.3, 2.4, 2.5, 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 2.4 Provide guarded no-autostart installation for daemon prerequisites
  - Extend the native package call with the backwards-compatible prevent_service_start keyword and an owned temporary deny-all policy transaction.
  - Preserve a known existing deny-all policy unchanged; fail before writes on foreign/conflicting policy or unresolved package-manager contention.
  - Journal temporary ownership, remove only unchanged owned policy on success/failure, and test interrupted recovery and edited-policy conflicts.
  - Keep protected-system script/trigger checks independent: denying service starts never permits kernel/boot/crypto changes.
  - Done when preview is non-mutating and disposable failure/recovery cases restore the original policy state without starting a forbidden daemon or overwriting foreign content.
  - _Boundary: PackageGuard_
  - _Depends: 2.3_
  - _Requirements: 2.1, 2.3, 2.4, 2.5, 5.6_

- [ ] 3. Preserve the per-user Node toolchain
- [ ] 3.1 Validate version and npm conflicts before changing user state
  - Validate the exact Node selection and diagnose conflicting user npm prefix/globalconfig settings and inherited overrides without exposing credentials.
  - Inspect the configured default alias target independently from the version it currently resolves to.
  - Keep user npm configuration intact and report the specific corrective action for conflicting inputs.
  - Done when version/alias/conflict fixtures pass, including a moving alias resolving to the selected version and npm configuration containing unrelated entries.
  - _Boundary: NodeDeploy_
  - _Requirements: 2.4, 3.1, 3.4, 3.6_

- [ ] 3.2 Make user Node installation and Bash initialization repeatable
  - Reuse pinned nvm and the selected Node runtime with bundled npm/npx; keep each operation's shell initialization explicit.
  - Preserve the exact default alias and one additive marked Bash block; avoid repeated PATH entries and preserve unrelated shell content.
  - Back up changed user files and verify restoration of the managed Bash changes without deleting unrelated configuration.
  - Keep installation user-owned, leave any system Node installation alone, and retry partial installations through observed state.
  - Done when disposable-home provisioning exposes Node/npm/npx in new interactive Bash terminals, user globals require no sudo, and a second apply makes no changes.
  - _Boundary: NodeDeploy_
  - _Depends: 1.1, 3.1_
  - _Requirements: 2.2, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [ ] 4. Integrate the foundation workflow
- [ ] 4.1 Route existing package consumers through the foundation contracts
  - Review the existing CLI manifest and its resolved versions for native packaging and prohibited transition behavior; reject unresolved entries rather than fall back.
  - Replace direct system-package calls with guarded installation and order preflight/policy before package consumers.
  - Apply preflight to standalone entry points as well as the combined deploy; retain a Node-only path that needs no sudo.
  - Update executable usage examples alongside the integration to use locked execution, preview and terminal sudo authentication correctly.
  - Done when every current repository package installation uses the guard and combined/standalone entry points produce the intended operation order.
  - _Boundary: Integration — Deploy orchestration, Preflight, PackageGuard, PackagePolicy, NodeDeploy_
  - _Depends: 1.2, 2.4, 3.2_
  - _Requirements: 1.2, 2.1, 2.2, 2.3, 2.4, 4.1, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4_

- [ ] 4.2 Establish disposable end-to-end validation and verify non-mutating previews
  - Prepare an isolated Ubuntu target with the required local desktop-user context, fixture package sources, and test-time authentication arrangement.
  - Compare managed files and package state across dry runs, including initially missing policy pins.
  - Verify standalone and combined entry-point checks and that Node-only operation needs no sudo.
  - Done when the repeatable integration harness demonstrates preview leaves managed configuration and packages unchanged.
  - _Boundary: Integration validation_
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3_

- [ ] 4.3 Verify repeatability, preservation, and restoration
  - Apply the permitted workflow twice on the disposable target and confirm the second apply makes no changes.
  - Compare protected login, GPU, T2 boot/initramfs/module/firmware/audio support and original snapd block across runs; keep mic/camera/touchbar/suspend functional acceptance explicitly pending until live checks.
  - Exercise restoration of backed-up user and owned policy files, preserving unrelated configuration and the original prohibition.
  - Done when integration results demonstrate unchanged second apply and successful restoration limited to foundation-owned changes.
  - _Boundary: Integration validation_
  - _Requirements: 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 4.2, 5.1, 5.2, 5.3, 5.5, 5.6_

- [ ] 4.4 Verify policy failures and truthful partial-result reporting
  - Exercise authentication/download failures, prohibited installed runtimes, policy conflicts and prohibited package plans in the disposable harness.
  - Confirm failures stop affected work and retain nonzero status without fallback installation or deletion of user applications.
  - Confirm earlier successful operations and unresolved work remain distinguishable after a partial apply.
  - Done when integration results identify the exact failed or pending stage without claiming full deployment success.
  - _Boundary: Integration validation_
  - _Requirements: 2.4, 4.1, 4.3, 4.4, 4.5, 5.4_

## Implementation Notes

- Task1.1: Preflight implemented; independent review APPROVED; fresh unittest9/9 and compileall PASS. Entry-point wiring remains4.1. Git checkpoint pending author identity configuration.
