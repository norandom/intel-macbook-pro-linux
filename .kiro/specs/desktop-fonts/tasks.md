# Implementation Plan

All executable units target 1–3 hours. Foundation's reviewed package/preflight contract must be implemented and available before task 1; this plan does not approve or implement foundation tasks. Consumer visual checks remain pending until desktop/app consumers exist. No live deployment task is authorized by this document.

- [ ] 1. Establish the guarded font feature entry and validation fixtures
  - Add the optional local entry and typed public manifest with exact source pins, selected styles and validated rendering input.
  - Check the upstream foundation imports and package-policy prerequisite; fail clearly if unavailable and preserve shared root orchestration.
  - Provide disposable managed-root/home and archive fixtures for later component tests.
  - Completion: the optional preview reaches validation with a valid manifest, rejects invalid pins/paths/root targets, and makes no host font or package changes.
  - _Boundary: FontDeploy, FontManifest_
  - _Requirements: 1.1, 1.2, 4.1, 4.4, 4.5_

- [ ] 2. Build verified and recoverable public font state
- [ ] 2.1 Preserve owned-file history and scoped restoration
  - Record prior bytes/existence and installed digests, protect backup access, and refuse cleanup of files changed after installation.
  - Leave unrelated and private font files untouched and retain shared packages on restoration.
  - Completion: fixture restoration recreates overwritten files, removes unchanged created files and reports edited-file conflicts without modifying them.
  - _Boundary: FontState_
  - _Requirements: 2.1, 4.2, 4.3, 4.5, 4.6_
- [ ] 2.2 Stage and publish source-pinned public font families
  - Acquire HTTPS artifacts, verify archive/file hashes, selected members and public licensing notices before publishing any family.
  - Reject traversal/symlinks, restore the previous family after publication/cache failure and replace marker-only predicates with file digests.
  - Completion: fixtures show ten selected Nerd styles and two Fixedsys files, invalid downloads preserve previous bytes, and a second unchanged apply avoids cache work.
  - _Boundary: FontArtifacts_
  - _Depends: 2.1_
  - _Requirements: 1.1, 1.2, 1.4, 4.2, 4.3_

- [ ] 3. Add user-preserving matching and core-font registration
- [ ] 3.1 Offer source rendering and fallback defaults additively
  - Generate the owned XDG fragment, retain user fonts.conf byte-for-byte and apply RGB/grayscale with emoji bitmap exception.
  - Detect unloaded fragments and conflicting effective preferences; preserve explicit values and return partial status instead of forcing defaults.
  - Completion: disposable-home checks resolve expected defaults without conflicts, retain preexisting overrides and report each conflicting requested preference.
  - _Boundary: FontconfigFragment_
  - _Depends: 2.1, 2.2_
  - _Requirements: 1.3, 2.1, 2.2, 2.3, 2.4, 4.2_
- [ ] 3.2 (P) Prepare indexed public Fixedsys copies
  - Build the dedicated core directory from verified Fixedsys content and generate scale/directory indexes only when inputs change.
  - Validate both family entries before publication; expose index failure separately from successful font artifacts.
  - Completion: fixture indexes name both fonts and corruption triggers repair without modifying unrelated font directories.
  - _Boundary: CoreFontIndex_
  - _Depends: 2.1, 2.2_
  - _Requirements: 3.1, 4.2, 4.3, 4.6_
- [ ] 3.3 (P) Implement the bounded desktop font-path helper
  - Adapt the source helper to the agreed executable, inherited display authorization and exact font-path entry contract.
  - Serialize concurrent per-display calls with nonblocking lock failure, retain the 40 half-second wait limit and propagate query/add/rehash failures with defined exits.
  - Completion: stub-display checks prove skip, timeout, argument rejection, exact-match idempotence and unchanged unrelated font paths; desktop configuration remains untouched.
  - _Boundary: XFontHelper_
  - _Depends: 1_
  - _Requirements: 3.2, 3.3, 3.4_

- [ ] 4. Integrate font phases through the optional guarded entry
  - Connect reviewed native package requests, receipts, artifact publication, additive configuration, core indexing and helper installation in prerequisite order.
  - Expose changed/unchanged/skipped/pending/failed results and keep absent private fonts optional/unavailable.
  - Completion: disposable integration preview changes nothing, apply/reapply converges, and scoped restore returns previous managed bytes while preserving user files.
  - _Boundary: Integration_
  - _Depends: 2.1, 2.2, 3.1, 3.2, 3.3_
  - _Requirements: 1.4, 2.4, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [ ] 5. Verify native family, glyph and display contracts
  - Add meaningful integration checks for actual family/style names, font coverage, fallback queries, RGB/grayscale properties and core XLFD discovery.
  - Exercise policy-denied dependencies, unavailable artifacts, missing display and user preference conflicts; report session checks pending where consumers are absent.
  - Completion: automated fixtures pass; the executable acceptance checks identify the actual selected files and mark unperformed terminal/widget/Xwayland visual checks pending without claiming runtime acceptance.
  - _Boundary: Integration_
  - _Depends: 4_
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_
