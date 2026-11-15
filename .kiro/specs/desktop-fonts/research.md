# Research & Design Decisions

## Summary
- Feature: desktop-fonts; extension of local provisioning, light integration discovery.
- Reviewed on 2026-11-15. Source revision: `a1c09ec3f02a98b7c6a4641f907108a2ad080993`.
- Findings: source font pins are reusable desired data; destructive user fonts.conf replacement and version-marker-only checks need adaptation; X11 core fonts require separate indexing and per-server registration.
- Skills consulted: kiro-spec-init, kiro-spec-requirements, kiro-spec-design and kiro-spec-tasks, including their rules/templates. Applied EARS, requirements/design pre-write gates, boundary-first synthesis, numeric traceability and bounded task sanity gate. All four agent slots were occupied at sanity review, so review mode is inline.

## Research Log

### Local project and foundation
Read AGENTS.md, this feature's brief, roadmap, package-policy, source-port plan and foundation design. Only Node and CLI runtime tasks exist; `manage/` and `tests/` are absent. Foundation's documented PackageRequest/PackagePlan and guard functions must be reused exactly. No root orchestration edits belong to this feature.

Core steering `product.md`, `tech.md`, `structure.md` is absent; roadmap and package-policy are the available project steering. This is a context limitation, not an invented implementation approval or font design blocker. Existing foundation task approval remains untouched.

### Pinned source audit
Read `/tmp/t2-source-audit/tasks/fonts.py`, font defaults in `group_data/all.py`, and private-font behavior in `tasks/private.py`. The source installs ten Nerd Font style files, two public Fixedsys files, regenerates Fontconfig caches and copies Fixedsys into the core directory. Nerd Font `.v{version}` markers alone miss damaged/missing files. Private source cleanup deletes files not in the decrypted inventory; exclude that path entirely because no private fonts were supplied.

Fetched actual pinned files through the GitHub plugin:
- [fontconfig template](https://github.com/norandom/hyperland-forky-worker-vm/blob/a1c09ec3f02a98b7c6a4641f907108a2ad080993/templates/fontconfig/fonts.conf.j2), blob `b4b8c15e4853a173447ebca6150aea03d6198c8b`.
- [hypr-xfonts](https://github.com/norandom/hyperland-forky-worker-vm/blob/a1c09ec3f02a98b7c6a4641f907108a2ad080993/files/bin/hypr-xfonts), blob `b58b022f3ce782380c6c2131089edb0e61f2788a`.

Template enables antialiasing/hinting/hintslight, RGB or grayscale, emoji embedded bitmap exception, JetBrainsMono monospace and weak emoji/Symbola fallback. Helper uses `/usr/local/share/fonts/x11-core`, waits in half-second intervals, adds its path and rehashes. Preserve public behavior while adding exact-entry checks, explicit diagnostics and concurrency handling.

### Official native contracts
[Fontconfig user documentation](https://fontconfig.pages.freedesktop.org/fontconfig/fontconfig-user.html) identifies XDG fontconfig/conf.d and fonts.conf, family matching and property editing. User configuration inclusion is controlled by the effective global configuration: an additive fragment is conventional but must be verified loaded. Explicit user preferences can conflict with the desired source defaults; report the difference instead of rewriting the user's main file.

[X.Org xset manual](https://xorg.freedesktop.org/archive/X11R7.5/doc/man/man1/xset.1.html) documents font-path addition and rehash. [X.Org font installation](https://xorg.freedesktop.org/archive/X11R7.5/doc/fonts/fonts.html) distinguishes core font indexes from Fontconfig. Installed file discovery is therefore insufficient proof of Xwayland core-font availability.

Ubuntu package pages verify native [xfonts-utils](https://packages.ubuntu.com/noble/xfonts-utils), [x11-xserver-utils](https://packages.ubuntu.com/noble/x11-xserver-utils) and [fonts-symbola](https://packages.ubuntu.com/noble/fonts-symbola); the official [file list](https://packages.ubuntu.com/noble/amd64/x11-xserver-utils/filelist) contains xset. These noble pages demonstrate package roles only, not this host's versions. The Noto package page and xfonts-utils file-list retrieval failed; local metadata supplies host evidence below.

### Actual host read-only observations
`/etc/os-release`: Ubuntu 26.04.1 LTS, resolute. `apt-cache policy` returned these native candidates from resolute repositories:

| Package | Observed candidate | Installed |
| --- | --- | --- |
| fontconfig | 2.17.1-3ubuntu1 | Yes |
| xfonts-utils | 1:7.7+7build1 | Yes |
| x11-xserver-utils | 7.7+11build1 | Yes |
| fonts-noto-color-emoji | 2.051-1build1 | Yes |
| fonts-symbola | 2.60-4 | No |
| x11-utils | 7.7+7build1 | Yes |

`fc-conflist` and `fc-match` executables exist. This is metadata evidence, not a new package simulation, dependency review, font installation, display connection or runtime validation. Re-simulate through foundation against current indexes before any installation.

## Architecture Pattern Evaluation

| Option | Benefit | Limitation | Decision |
| --- | --- | --- | --- |
| Copy source fonts.py/template unchanged | Closest text reuse | Overwrites user configuration; marker-only checks | Reject unchanged copy |
| Small pyinfra components plus native font utilities | Existing execution model; scoped ownership | Requires explicit receipts and diagnostics | Adopt |
| General font-management service | Potential central registry | Unneeded runtime and broader ownership | Reject |

## Design Decisions
- Generalize artifact metadata only across the four current public inputs; no generic binary installer. Reuse Python/native utilities rather than a font daemon or new package ecosystem.
- Preserve source pins and destinations; strengthen staging and digest predicates. Pin correctness must be checked against downloaded bytes during implementation; no downloads or checksum recomputation occurred here.
- Use additive XDG fragment and conflict reporting. Preserve source rendering defaults as offered values, default grayscale for potentially scaled laptop use; source RGB RDP default remains explicitly selectable.
- Fonts owns helper bytes, directory and exit semantics; desktop owns invocation. No dependency on missing GPU unit evidence.
- Private font inventory is optional/unavailable. No family list was supplied, so do not invent proprietary names or fetch encrypted source payloads.

## Risks & Mitigations
- User configuration precedence can prevent desired defaults: verify loaded fragment and effective queries; report partial status.
- Fixedsys XLFD exposure depends on Xwayland's font backend: verify indexed names via xlsfonts and a legacy client after desktop exists.
- Foundation guard not implemented: explicit prerequisite task and no direct apt fallback.
- Source artifact/license availability can change: validate pins, selected members and license notices before publishing; fail without altering working fonts.

## Validation Performed and Pending
Performed: source reads, actual GitHub pinned template/helper fetches, official documentation lookup, read-only OS/package metadata, document traceability and inline review. Pending: artifact downloads/digests, archive member and license verification, apt dependency simulation, implementation tests, dry/apply/reapply/restore, actual font matching, live glyph rendering and Xwayland checks. Document completion is not software acceptance.
