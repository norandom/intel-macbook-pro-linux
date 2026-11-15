# Research & Design Decisions

## Summary
- Feature: shell-user-tools; complex source integration, full discovery with code/API/official-doc review on 2026-11-15.
- Source root revision: `a1c09ec3f02a98b7c6a4641f907108a2ad080993`; local inspected snapshot `/tmp/t2-source-audit`, provenance `.kiro/source-repository-index.json`.
- Actual source helper inspection overturned misleading deployment comments: reclamation deletes by default, including container volumes; this is not accepted on the laptop.
- nvim-simple source pin leaves vim-plug and five plugins moving. Source configuration pin alone is not a reproducibility/compatibility claim.
- nvm forbids the source `.npmrc prefix=~/.local` arrangement. Native applications and user tool packages remain different owners.

## Research Log

### Source shell and P10–P13
Read complete `tasks/shell.py`, `tasks/user_tools.py` and matching `group_data/all.py` values in the snapshot. Fetched missing assets at root revision using connected GitHub fetch_file, without changing upstream:

| Asset | Verified blob SHA | Behavior and decision |
|---|---|---|
| files/bash/grml.bash | 5163aba4a8490d05fac1f95379a2085a73caf6c4 | interactive guard, shopt, colors, directory helpers, prompt, Hyprland keyboard redirect; preserve behavior with session gating/status/idempotency fixes |
| files/bin/dev-disk-reclaim | f185bce7f01ceb31ffd3c30317a36d14c3d96398 | APPLY=1, DO_VOLUMES=1, apt autoremove, forced caches and general tmp deletions; remove dangerous branches and make all scheduled runs reports |
| tasks/shell.py | 0b1332f99c0a928731de910de5ecb5dc8b16cd86 | source history/readline values, startup gh token export, hardcoded uutils path and xfconf; preserve shell values, reject credential export, defer uutils, terminal configs belong to themes |
| tasks/user_tools.py | f880044c4485f0e570544e2c118116ee0f39f5aa | pinned nvim/SafeChain/ax but moving npm/uv/skills, overwrite/delete/error masking and hostname roles; replace with explicit staged routes |

Canonical asset links: [grml source](https://github.com/norandom/hyperland-forky-worker-vm/blob/a1c09ec3f02a98b7c6a4641f907108a2ad080993/files/bash/grml.bash), [reclaim source](https://github.com/norandom/hyperland-forky-worker-vm/blob/a1c09ec3f02a98b7c6a4641f907108a2ad080993/files/bin/dev-disk-reclaim). Source commands specify `kubectl completion bash`, `helm completion bash`, `gh completion -s bash`, `ax completion bash`, `rc completions bash`; actual installed versions must still pass command/syntax checks.

### Backlog disposition
| Item | Adopted behavior | Exception or owning neighbor |
|---|---|---|
| P10 | pinned nvim-simple, five plugins, CUA/menus/Berg, backups/errors | desktop theme bridge belongs to coordinated-themes |
| P11 | pnpm/SafeChain/Copilot/Codex/ccusage/euporie+kernel/pretty-mermaid/ax/completions | exact unpinned tool/plugin inputs are required intake locks; auth remains manual |
| P12 | explicit mounts/cache-report timer/Quarto Python/TinyTeX profiles | TinyTeX blocked pending immutable artifact review; no inherited remote/hostname role |
| P13 | grml/readline/history/prompt/helpers, conditional turbo consumer | token export rejected, uutils deferred optional, terminal/xfconf settings delegated to themes |

`tasks/private.py` was read: it installs license clipboard helper/menu entries, private fonts and Sublime licenses, including source-side private-font pruning. All private archive/key/font/license transfer and prune branches are excluded here; no private archive is opened. Fonts/application/desktop owners may later consider public behavior, but no credentials or license helper is silently ported by shell tools. Mounts use only owner-created remote names, never source remote secrets.

### Editor pinned API
[init.vim at selected pin](https://github.com/norandom/nvim-simple/blob/70717b469ce15ade8b1186c3650a484a5202cb75/nvim/init.vim) fetched successfully; blob `1a8ae31ec7227fc72e2ab00136228c146b5f132d`. Five verified plugin declarations: vim-quickui, vim-airline, vim-airline-themes, nerdtree, vim-devicons. Vim-plug bootstrap fetches master. CUA, menu/explorer/terminal/tab keys and `ToggleTheme()` were inspected. Devicons/powerline are disabled, so no glyph-font dependency is added. Source forcibly sets locale/TERM; validate available locale and terminal behavior during staging rather than claim compatibility.

Pinned color directory inspected: `berg.vim` blob `b96283cf7ba39a8ed2e3d4b1bc2565f8383d1f07`, `berg-light.vim` blob `edfcc4826dffcd15b4b7d02f9c8704e38558a30f`. [vim-plug official options](https://github.com/junegunn/vim-plug#plug-options) supports immutable commit selection. Exact plugin/vim-plug commits and tested Neovim version remain implementation intake gates; none is guessed. Source plugin failure `|| true` and broad Lazy/Mason deletion are rejected.

### Safe Chain release versus template
Source data sets 1.5.25 and installer SHA256 `83069f6db4215cccf6a26bdd6e65a5c2366b9d24322b2d5d2862d47385e56682`. [Tagged installer source](https://github.com/AikidoSec/safe-chain/blob/1.5.25/install-scripts/install-safe-chain.sh) fetched (blob `5f73c533964853f6a38452890be2c920885d3818`): template VERSION may fetch latest, binary checksum placeholders are empty, installation may uninstall npm/Volta/nvm Safe Chain and runs setup; setup failure only warns. This source template is not the generated release artifact. The actual source-pinned release download and its binary digest have not been downloaded or verified in this run; feature must remain blocked until review completes.

[Tagged shell-integration docs](https://github.com/AikidoSec/safe-chain/blob/1.5.25/docs/shell-integration.md), blob `d6cc0e0a8969749fa10e1a31f4f3b6a6183f47d6`, confirm setup/teardown edits multiple shell profiles, `aikido-*` commands and manual shell functions. [Tagged README](https://github.com/AikidoSec/safe-chain/blob/1.5.25/README.md) documents per-package-manager safe-chain-verify. Adopt only staged reviewed files with our loader, preserve foundation block, diagnose wrappers and explicitly verify noninteractive invocation. These docs do not prove selected-runtime compatibility or release binary integrity. Main-branch documentation was inspected for context only and does not replace the 1.5.25 API gate. A guessed setup.ts path returned 404; actual JS source directory was listed, no API inferred from that failed lookup.

### Toolchain and package isolation
[nvm official npm configuration](https://github.com/nvm-sh/nvm#npm-configuration) documents incompatibility with npm prefix overrides. [uv official tool guide](https://docs.astral.sh/uv/guides/tools/) supports isolated tool environments and versioned tools. Use foundation nvm/uv, no second uv install, no user prefix rewrite. euporie/ipykernel and npm/skill package versions/dependency integrity require explicit committed lock review before application; source supplied no exact versions.

[ax v0.3.1 go.mod](https://github.com/google/ax/blob/v0.3.1/go.mod), blob `3f8918d3d03bb9bd98d10ac591810b0ef23abe6d`, declares Go1.27.1; source GOTOOLCHAIN=go1.27.2 satisfies declared minimum only. This does not prove a build, toolchain availability/checksum or runtime API. Keep source module/toolchain pin with explicit download review and private build caches; no `go clean -modcache` across owner's projects.

### Optional routes
[rclone mount official docs](https://rclone.org/commands/rclone_mount/) describe FUSE and systemd readiness/foreground behavior. Source rclone units use Type=notify, ExecCondition, full VFS/2G cache and fusermount3; adapt binary paths to application availability and validate service/remote/empty mountpoint before start. No remote authentication imported.

[Quarto Python guide](https://quarto.org/docs/computations/python.html) confirms selection through QUARTO_PYTHON. Source package list: nbclient0.11.0, nbformat5.11.1, ipykernel7.4.0, jupyter-client8.10.0, pyyaml6.0.3. Full dependency lock and interpreter compatibility remain unverified. TinyTeX source command downloads another distribution; immutable release/dependency/install-path review is an explicit blocked optional route. No claim of pinned TeX or successful render.

### Cross-spec and strict preservation
Read foundation design and relevant tasks; resource-policy, application-suite and desktop-fonts designs. Only exact foundation preflight/PackageRequest/guard functions are consumed. Source artifact routes are feature-reviewed rather than invented foundation APIs. Application report schema_version=1 uses stable IDs and executable re-probes. Resource owns turbo.bash and aliases; shell never modifies their content. Themes owns terminal files and nvim plugin bridge. Read package, desktop-audio, T2 hardware, protected-system and keyboard steering. product.md, tech.md, structure.md are absent; no replacement steering invented.

Protected-system no-go supersedes permissive source cleanup/package/build assumptions: kernel/initramfs/LUKS/LVM/storage/boot changes and hooks are forbidden. Simulated package lists alone do not prove safe triggers. Preserve graphical German Mac/Option+L/source Super through desktop's helper; no console or unlock keymap changes.

## Architecture Pattern Evaluation
| Option | Strength | Limitation | Decision |
|---|---|---|---|
| Copy upstream deploy modules | Fast feature visibility | prefix conflicts, credential export, deletes and VM assumptions | rejected |
| Small feature modules/native user units | Clear ownership, minimal framework, testable staging | needs intake locks and explicit runtime gates | adopted |
| General package installer abstraction | Potential reuse | duplicates foundation and hides privileged scripts | rejected |

## Design Decisions

### Adopt source behavior through bounded native components
Generalize only immutable manifest/status/backup handling shared by this feature. Keep shell/editor/tools/optional units cohesive, with native nvm/uv/systemd and no daemon. Stage network artifacts before publishing and defer only capabilities whose required inputs are unverified; expose that status. This preserves source features while avoiding a generic infrastructure spec.

### Separate shell and theme writes
Use a distinct shell loader and per-file editor publishing with explicit exclusion for theme-owned plugin. Whole-directory destructive Neovim replacement is rejected because it races downstream palette ownership. Resource fragment is consumed conditionally without changing CPU state.

### Change cache behavior intentionally
The requested safe laptop behavior conflicts with source helper's actual delete default; design explicitly changes it to report-only. Exclude protected/system/container data branches rather than merely add an opt-in flag. Optional timer is reporting only. File rollback cannot reverse manual deletion.

## Risks & Mitigations
- Safe Chain generated release differs from source template: stage/verify exact release and wrapper coverage; keep blocked until proven.
- Moving plugins/packages/skills: resolve immutable locks and review install behavior before any selected install; no fabricated versions.
- App prerequisites may be blocked: core shell can proceed independently, selected affected capabilities fail clearly.
- Clipboard, key handling, user-bus mounts and physical T2 behavior need live session checks; docs cannot certify them.
- Foundation implementation/task approval is upstream readiness, not completed here. Guard all native hooks and protected targets before application.

## Review Method and Evidence
Applied kiro-spec-init, kiro-spec-requirements, kiro-spec-design and kiro-spec-tasks skills and their templates; EARS, requirements review, full discovery, synthesis, design principles/review, task generation and parallel-analysis rules were read. Requirements and design review were inline with bounded local repair; task graph gets a fresh independent reviewer where available. Detailed verdicts are in review.md. All research is read-only inspection/fetch; no installer, package operation, plugin execution, cleanup, live service or physical test ran.
