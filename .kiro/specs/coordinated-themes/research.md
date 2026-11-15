# Research & Design Decisions

## Summary
Extension/integration discovery used actual source revision `a1c09ec3f02a98b7c6a4641f907108a2ad080993`, the revised brief/roadmap, finalized desktop-fonts and shell-user-tools specifications, desktop consumer-contracts.md and all six present custom steering files. Default product.md, tech.md and structure.md are absent; no replacements were invented. Consulted phase skills: kiro-spec-init, kiro-spec-requirements with EARS/review rules, kiro-spec-design with light discovery/principles/synthesis/review gate, and kiro-spec-tasks with generation/parallel rules/templates. Batch `-y` permits phase approval after review, never bypasses gates.

## Research Log

### Actual source assets and generators
- Inspected `/tmp/t2-source-audit/tasks/themes.py`, desktop.py, shell.py, user_tools.py, `files/bin/hypr-term`, hypr-termtheme, Terminator config/plugin, nvim bridge and both generators.
- Retrieved all 39 files under source foot/Ghostty/Sublime/themes/VSCode asset directories via connected GitHub at the exact revision. Compared each Git blob SHA1 with `.kiro/source-repository-index.json`; all 39 matched. SHA256 values are recorded in source-assets.json.
- Ran both original generators in disposable `/tmp/themegen-audit-*` staging populated with those actual files and original Terminator inputs. Both exited0; every checked-in asset output remained identical. This is real offline source reproduction, not Ubuntu application/runtime acceptance.
- Actual complete inventory: five Terminator profiles plus tab dictionary and menu; five Ghostty theme files plus five CSS files; five foot INIs; five btop themes; five Claude custom JSONs; five Sublime schemes; one Code/Positron local extension manifest with five theme JSONs; one constant Chromium policy; terminal base configs; cobalt-only xfce block; one next-start Neovim bridge. Code/Positron share the same six extension files. All application targets are optional selections beyond source-default Terminator; installations stay application-owned.
- Generated themes retain 16 ANSI colors and editor schemes retain 16 token rules each. Exact editor/terminal backgrounds/foregrounds are documented in design; matching three colors alone is insufficient asset reuse.

### Source behavior and explicit adaptations
Source order is default/navy/fixedsys/cream/petrol, default maps cobalt. hypr-term execs Terminator `-p` with argument preservation. Source writes state before app mutations; uses broad pkill; regex-strips JSONC and whole-file rewrites; deletes old Ghostty config. Port changes these to journaled commit-last selection, session/process-verified reload and token-preserving edits, with unsupported configs untouched.

Source `apply` re-applies application themes without cycling and exits before Terminator/Waybar/notification actions. Preserve this consumer behavior. Source Neovim bridge only explicitly selects light for cream because the base defaults dark; port explicitly selects light/dark on next startup against validated shell base, preserving manual toggle. Source xfce4-terminal remains cobalt-only and unsafe-paste review=true; it is not an invented five-theme source participant. GTK styling is terminal-selector scoped; preserve global GTK/KDE preferences.

### Public compatibility references consulted
- [Ghostty configuration](https://ghostty.org/docs/config): config.ghostty is current name since1.2.3; prior config remains relevant. [Ghostty systemd/Linux](https://ghostty.org/docs/linux/systemd): reload through tracked process/SIGUSR2. These verify current interface direction, not compatibility of an unprobed installed release or all source options.
- [Terminator remotinator source](https://github.com/gnome-terminator/terminator/blob/master/remotinator) and [IPC source](https://github.com/gnome-terminator/terminator/blob/master/terminatorlib/ipc.py): switch_profile_all command exists upstream. Installed Ubuntu version/bus/profile behavior remains an explicit runtime prerequisite.
- [VS Code JSON editing](https://code.visualstudio.com/docs/languages/json): JSONC/comments/trailing commas are supported settings syntax. [Settings](https://code.visualstudio.com/docs/configure/settings) and [Themes](https://code.visualstudio.com/docs/configure/themes): theme/font settings and color-theme selection. Port cannot safely parse those files using source regex removal/whole-document serialization.
- Source themegen.py explicitly targets foot>=1.26 `[colors-dark]` cursor dialect. Do not assert Ubuntu's installed foot meets that minimum; native parser/version probe and documented dialect adaptation or incompatible result precede writes.
- Claude custom themes, Positron contribution engine, actual GTK CSS and Chromium native policy support require selected installed-version probes. Directory/executable presence alone is insufficient proof.

## Architecture Pattern Evaluation
| Option | Benefits | Limitations | Decision |
| --- | --- | --- | --- |
| Copy source deploy/scripts verbatim | Maximum source text reuse | Destructive config rewrite, early state commit and broad process signaling | Reject unsafe operations; retain actual assets and CLI |
| Generic theme management framework | Extensible | Unneeded runtime/dependency ownership | Reject |
| Small source-derived adapters and journal | Clear target preservation and stable consumer seam | Must validate each installed format/reload | Selected |

## Design Decisions
Generalize only typed target preparation/result handling, while retaining source-specific paths and settings. Adopt native app mechanisms and existing foundation policy rather than a new service or installer. Use standard-library lexical span edits for the narrow root-key JSONC seam so runtime needs no Node environment; reject ambiguous/unsupported syntax rather than guess. Unit fixtures must prove preservation before publication.

Compatibility selection commits last, with per-file journal and bounded private locking because independent app directories cannot share a single atomic rename. External reload is postcommit and explicitly pending on failure; avoid false all-app atomicity. xfconf and privileged Chromium policy are separate provisioning transactions rather than runtime cycle work.

Do not broaden into app installers, compositor builds, keyboard/audio adjustment or KDE adaptation. Native Ubuntu Hyprland0.53.3 backport is desktop-owned. Themes work without compositor and finalized producer contract is upstream of desktop finalization.

## Risks & Mitigations
- App upgrades change config grammar/options: re-probe installed versions and leave unsupported bytes untouched.
- Concurrent editor writes or interrupted switch: input digests, private nonblocking lock, durable journal and conflict-aware recovery; no claim of cross-directory atomicity.
- Berkeley Mono absent: preserve original requested profile family and document actual public monospace fallback; no private extraction.
- Global GTK/Chromium policy interference: scoped terminal selectors/import and opt-in browser-specific file with conflict inspection.
- Foundation guard/editor/font designs exist but implementation is not proven: expose prerequisites; no bypass apt, no forced app install, ready_for_implementation remains false until actual prerequisites are available.

## Validation Status
Passed during specification: pinned asset Git-blob verification, both offline source generators and unchanged output comparison, numeric requirement/design/task coverage inspection. Planned only: implemented fixtures, installed config parsers, live app color/reload/clipboard/keyboard/hardware and standalone Hyprland integration. Protected configuration was not mutated. No deployment, package install or live acceptance was performed.
