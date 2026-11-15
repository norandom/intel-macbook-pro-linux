# Research and Design Decisions

## Summary
Extension/integration discovery. Inspected the complete pinned tasks/apps.py,
group_data release_tools/client_debs/artcraft_apps and source tree. All literal
apt entries are recorded in source-inventory.md, with local metadata preserved
in package-candidates.txt. No package was installed during this work.

## Research Log
- Source revision a1c09ec3f02a98b7c6a4641f907108a2ad080993, upstream files
  available in /tmp/t2-source-audit during this session; committed inventory
  retains provenance beyond that temporary location.
- Local apt-cache policy lists many native candidates but chromium and
  chromium-driver have no candidate. A candidate is not a verified safe route.
- [Chromium official downloads](https://www.chromium.org/getting-involved/download-chromium/)
  distinguishes testing builds and arbitrary Chromium snapshots from stable
  user builds. No browser alternative is silently selected.
- [VS Code Linux installation](https://code.visualstudio.com/docs/setup/linux)
  offers .deb and repository routes; these require a reviewed compatible route
  outside the foundation's Ubuntu-only PackageRequest before local use.
- Official Ghostty/Ubuntu doc fetches failed; no compatible Ghostty build is
  claimed. Reject the source forky .deb for this Ubuntu host.
- Kiro requirements/design/tasks skills, light discovery, EARS and review gates
  informed numeric traceability, explicit blocked states and task boundaries.

## Architecture Pattern Evaluation
Use an inventory/selection contract with native guard and a narrowly reviewed
archive installer. Reject a generic arbitrary installer shell or unconditional
copy of vendor repos. Keep native binary ownership distinct from feature configs.

## Design Decisions
- Complete source coverage is mandatory; optional and blocked routes remain
  visible rather than being silently omitted.
- Foundation guard remains Ubuntu-only. Standalone archives use the explicit
  reviewed-feature artifact allowance; no invented PackageRequest source type.
- Vendor/.deb route support remains an explicit unsupported route requiring
  further compatible installer design. Such selected required apps fail rather
  than install through an unsafe or guessed mechanism.
- Favor native pyinfra operations and small typed modules; no new dependency
  or provisioning framework. No speculative cross-app settings abstraction.

## Risks and Mitigations
Native maintainer-script/repository drift requires re-review of exact selection;
source digest strings are not proof of Ubuntu compatibility. Archive extraction
is restricted to known members with traversal/link validation. All repeated
operations compare actual executable state. Source-role purges are excluded.

## References
See links above and foundation design for exact PackageRequest interfaces.
