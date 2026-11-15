# Research and Design Decisions

## Summary
- Feature: hyprland-rdp; complex integration, source-led greenfield local port.
- Owner selects unmodified upstream maintainer archive; compositor remains Ubuntu0.53.3.
- Upstream0.54+ declaration conflicts with unproven native0.53 runtime support; bounded activation gate preserves that discrepancy without pretending it is resolved.
- No artifact downloaded or runtime/client/hardware tests performed for this spec.

## Research Log
### Source versus maintained upstream
Inspected pinned source a1c09ec3f02a98b7c6a4641f907108a2ad080993 under /tmp/t2-source-audit: tasks/hypr_rdp.py, tasks/away.py, templates/hypr-rdp config/unit and session/sessionwatch/modecache scripts. Source patched build/package, generic graphical target, log-derived hooks, journal-group membership, audio redirect, Virtual-1/QEMU device suppression and unlock signal are inappropriate for the laptop. away.py changes root sudo/ptrace policy and is excluded explicitly. Source mode cache should not be copied as a global polling daemon; selected-session authoritative observations replace it only where needed.

### Tagged maintainer interfaces
Read tagged v0.1.8 README and Cargo metadata under /tmp/t2-hypr-rdp-upstream; independently fetched the tagged README through web tooling. It documents supported configured credentials/password_file, mirror/off audio, compositor keyboard policy, wlr/ext capture, upstream ClearCodec, optional file transfer/FUSE and native session hooks. Upstream hook subprocesses may survive their10s wait, requiring helper-side deadlines and stale-token rejection. README0.54+ remains authoritative declared support, not rewritten by our observations.

Inspected src/hyprland.rs and src/hyprland/monitor_ipc_tests.rs. Monitor configuration attempts Lua eval first and then legacy keyword after delivered parser rejection; transport failure is not replayed. The tagged test exercises one compatible fallback path, not capture/input/codec/server viability on0.53. Explicit selected identity is still supplied by the desktop contract because upstream discovery itself is not an authorization boundary.

### Archive and ABI
upstream-release-notes.md records v0.1.8 release API metadata: size8936327 and SHA256 f8b324fcf5c169dd4df269685294db55078b4d6a28cd47a6a86e00d35671b0fd. The API URL fetch through web tooling was inaccessible; existing recorded metadata is a candidate pin, not a new verification. Actual archive integrity, member inventory, ELF architecture/interpreter/NEEDED/symbol versions, dependency safety and runtime behavior are implementation gates. Build workflow ubuntu-latest does not establish target ABI compatibility. No substitute fork/rebuild path.

### Producer contracts and protection
Read finalized desktop design/consumer-contracts, finalized themes contract, roadmap and all protected-system/T2/keyboard/audio/package steering. RDP consumes hypr-session status schema1 and owns no desktop/theme configuration. Rootless-containers dependency supplies final assembled evidence, not a compositor build. Core steering product.md,tech.md,structure.md do not exist; this is a context limitation, not authority to invent policy. User's German Mac baseline includes source Super arrangement and left Option level3, retained as compositor keyboard policy. Hardware inventory is not live verification.

### Cross-spec placement ownership amendment (2026-11-15)
Re-read finalized `../hyprland-desktop/design.md` (HyprIPC and WindowWorker), `../hyprland-desktop/consumer-contracts.md` and RDP requirement3.3/4.1. Desktop normalizes internal clients/monitor query state and owns monitor-topology/removal placement recovery; its consumer contract exports selected-session status, not a placement-snapshot service. The earlier RDP design/task4.2 assumption of consumable authoritative worker snapshots had no producer API. Removed that dependency and RDP-specific window rescue. RDP owns remote-output cleanup, while its diagnostics/assertions use only bounded read-only selected-instance native0.53 `clients`/`monitors` observations before/after output removal, a finite settling deadline and explicit failed/pending evidence. No private worker access, new snapshot producer contract, duplicate placement policy or compositor dispatcher is introduced. Requirements and their approved scope remain unchanged; prior batch approvals are retained as historical approvals, and independent amendment cross-review is pending. All implementation tasks remain unchecked; no native/client/hardware recovery is verified. Consulted kiro-spec-design for boundary/discovery guidance and kiro-verify-completion for a documentation-only evidence gate. Core steering defaults remain absent as previously recorded.

## Architecture Pattern Evaluation
| Option | Decision | Reason |
| --- | --- | --- |
| Port source fork and watchers | Rejected | Owner forbids fork/build; stale journal/VM assumptions |
| Maintainer archive plus bounded selected-session helpers | Selected | Supported config/hooks, smallest ownership seam |
| Upgrade compositor to documented minimum | Rejected | Owner fixed native0.53 baseline |

## Design Decisions
Adopt upstream server and current documented options. Build only feature-local validation/receipts/hooks; no generic protocol framework. Consolidate activation identity and capability checks in one control path. Normal exposure is disabled until valid; deliberately invoked authenticated loopback diagnosis can generate compatibility evidence without assuming it. Failed native tests persist exact blocker and do not alter owner version choices. File transfer and optional codecs are gated independently. P23 aggregates existing checks rather than reproducing implementations.

## Risks and Mitigations
- Native0.53 may genuinely fail: report exact protocol/runtime failure and keep normal activation blocked.
- Archive may require newer libraries: inspect ELF before executing, use protected foundation plan or report blocked; no builds.
- Upstream hook timing/replacement races: bounded private helpers, run-token matching, idempotent cleanup and target-stop reconciliation.
- Live T2/GPU/client evidence unavailable: keep affected acceptance pending, especially missing GPU unit.

## References
- [Tagged upstream README](https://github.com/MuNeNiCK/hypr-rdp/blob/v0.1.8/README.md)
- [Tagged monitor IPC](https://github.com/MuNeNiCK/hypr-rdp/blob/v0.1.8/src/hyprland.rs)
- [Tagged IPC tests](https://github.com/MuNeNiCK/hypr-rdp/blob/v0.1.8/src/hyprland/monitor_ipc_tests.rs)
- [Release](https://github.com/MuNeNiCK/hypr-rdp/releases/tag/v0.1.8)
- Local source provenance: .kiro/source-repository-index.json; docs/source-port-plan.md P21–P23.

Consulted kiro-spec-init, kiro-spec-requirements and EARS/review rules, kiro-spec-design full-discovery/principles/synthesis/review rules, and kiro-spec-tasks generation/parallel/sanity rules. Requirements/design gates ran inline. Batch intentionally supplies -y at design/tasks; no implementation is authorized by document approval.
