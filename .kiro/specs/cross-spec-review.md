# Independent cross-spec consistency review

## Verdict

PASS after one remediation round. Review mode: independent subagent, using the
session's available inherited model; the custom reviewer's configured gpt-5.4
was not available in the tool model catalog.

## Scope

All eight new source-port requirements/designs/task boundaries, the existing
foundation and pending GPU spec, source backlog, roadmap, producer/consumer
contracts and current owner steering constraints.

## First review and repairs

- Missing Terminator producer: application-suite now owns Terminator/remotinator,
  declared native dependencies and Xfe in the explicit Hyprland core profile.
- Undefined daemon start suppression: foundation now publishes the optional
  prevent_service_start contract and task2.4; resources uses the exact flag.
- Carlito ownership: latest owner direction deferred LibreOffice/Carlito and
  Craft suite completely; selection rejects current installation/configuration.
- Shared package records: cliphist delegates to desktop; x11-xserver-utils to fonts.
- Undefined RDP placement snapshots: desktop owns topology recovery; RDP uses
  selected read-only native IPC observations without a second placement API.

## Re-review result

Independent reviewer confirmed all reported issues resolved and no remaining
substantive document/contract/ownership contradictions. Native Ubuntu0.53
backport, decoration priority, upstream-only RDP archive, German Mac/source
Super mapping, dormant KDE/unchanged SDDM and protected-system/T2 preservation
align across the portfolio.

## Evidence limits

This review approves document consistency, not runtime compatibility or host
changes. The upstream RDP0.54+ support statement versus chosen0.53.3 desktop is
an explicit activation/test gate. Artifact integrity/ELF checks, actual hardware
acceptance and existing GPU-unit capture remain pending. All implementation
checkboxes remain unchecked. No source builds, package installation, boot or
storage changes were performed during specification generation.

## Verified portfolio counts

| Feature | Acceptance criteria | Executable tasks |
| --- | --- | --- |
| laptop-resource-policy | 26 | 11 |
| rootless-containers | 20 | 11 |
| desktop-fonts | 18 | 8 |
| application-suite | 20 | 7 |
| shell-user-tools | 33 | 20 |
| coordinated-themes | 22 | 18 |
| hyprland-desktop | 44 | 27 |
| hyprland-rdp | 21 | 14 |

Total: 204 criteria, 116 executable port tasks.
