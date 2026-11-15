# Implementation Plan

These tasks port source application capabilities and preserve a complete
explicit inventory. Vendor/.deb routes are visible follow-up work, not a claim
of supported installation. Each executable task is sized for 1–3 hours.

- [ ] 1. Capture the complete source manifest and ownership
  - Port literal application lists and release/client maps at the pinned revision;
    include provenance, expected executable, delegated owner and disposition.
  - Preserve full optional/vendor inventory instead of narrowing to CLI tools.
  - Done when source-to-manifest coverage checks find no missing or duplicate IDs,
    and source private credentials/license data are absent.
  - _Boundary: ApplicationCatalog_
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 4.3_

- [ ] 2. Validate selected routes and publish observed availability
  - Implement stable IDs, required/optional selection, native-origin/transition
    rejection and the versioned availability report contract.
  - Keep unknown/blocked route states explicit; a stale report never proves an
    executable exists. Observation and preview must remain read-only.
  - Done when selection and stale/missing/prohibited-route fixtures report the
    exact app and reason; selected required blocked entries fail before writes.
  - _Boundary: ApplicationCatalog, RouteValidation, Availability integration_
  - _Requirements: 1.2, 1.3, 2.2, 2.3, 2.4, 3.4, 5.1, 5.2, 5.3_

- [ ] 3. Port selected native application binaries through foundation policy
  - Reuse guarded native installation and reviewed exact package metadata;
    preserve delegated foundation/container/font ownership.
  - Include native Terminator/remotinator with configobj/GI/GTK/VTE dependencies and Xfe under explicit hyprland-core selection; publish availability IDs before theme/desktop consumers.
  - Provide the source app executable dependencies needed by downstream features
    only when selected and route-reviewed; never install a Snap transition.
  - Done when native candidate/install/report fixtures and a disposable Ubuntu
    smoke test expose expected executables while leaving unselected apps intact.
  - _Boundary: NativeApplications_
  - _Requirements: 2.1, 2.2, 3.1, 4.1, 4.4, 5.2_

- [ ] 4. Port reviewed standalone release artifacts safely
  - Capture source archive URLs/digests and review selected compatible versions,
    native dependencies, member names and executable/version contracts.
  - Verify checksums, prevent archive/link escape, avoid unmanaged binary
    conflicts and atomically replace only owned user binaries with restoration.
  - Done when mismatch/traversal/conflict/version-failure fixtures preserve prior
    state and selected valid archive installs pass an unchanged second run.
  - _Boundary: ArtifactInstaller_
  - _Requirements: 1.4, 2.3, 2.4, 3.1, 4.1, 4.2, 4.3, 4.4, 5.2_

- [ ] 5. Preserve deferred installer inventory and non-conflicting compatibility
  - Record LibreOffice/language/tabbed UI/Carlito and all source Craft installer entries as explicit backlog, with no current install/configuration operations.
  - Retain installer provenance and reject selecting backlogged entries until that work is explicitly reopened; preserve any existing apps/data.
  - Add non-conflicting fd compatibility only when needed, preserving existing local commands and unrelated settings.
  - Done when backlog fixtures generate no installer actions and compatibility-link conflict checks leave existing commands intact.
  - _Boundary: ApplicationCatalog and NativeApplications integration_
  - _Requirements: 1.1, 1.2, 1.3, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 4.4_

- [ ] 6. Integrate the optional application deploy and route report
  - Wire catalog, availability and installers through the feature entry point,
    using foundation preflight/policy and preserving root deploy ownership.
  - Include every unresolved vendor/.deb/client selection in generated route
    documentation; no fallback, silent skip of required apps or false success.
  - Done when preview shows changes/pending statuses without downloads/writes,
    and selected required errors retain nonzero exit with per-app results.
  - _Boundary: FeatureDeploy integration_
  - _Depends: 2, 3, 4, 5_
  - _Requirements: 1.3, 2.4, 3.4, 5.1, 5.2, 5.3, 5.4_

- [ ] 7. Verify application port replay and preservation
  - Exercise native and archive routes on a disposable target, source inventory
    coverage, dependency failures, blocked Chromium/vendor entries and rollback.
  - Verify no protected login/GPU/T2 boot writes and no secrets in reports;
    preserve all unselected app data and unrelated local configuration.
  - Done when acceptance tests demonstrate non-mutating preview, unchanged repeat
    apply, correct recovery and explicit unresolved source-feature status.
  - _Boundary: Integration validation_
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4_
