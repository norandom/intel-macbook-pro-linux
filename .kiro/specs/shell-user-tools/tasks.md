# Implementation Tasks: shell-user-tools

Entry point: `.venv/bin/pyinfra @local tasks/shell.py` (run after `tasks/node.py` and `tasks/tools.py`).
Pins/config: `manage/shell_tools.py`. Assets: `files/shell/`. Tests: `tests/test_shell.py`.

## Implemented
- [x] grml-inspired Bash (`~/.config/bash/grml.bash`): shopts, colour/grml aliases, `k=kubectl`, dir stack
      bounded to 20, `mkcd`/`cdt`/`bk`/`sll`/`ssearch`, user@host/dir/Git prompt with failed status (1.1)
- [x] Kali-style shared timestamped history (`history.bash`); hooks keep `$?`, added once, scalar or
      array `PROMPT_COMMAND` (1.2, 1.3)
- [x] Readline prefix Up/Down search + case-insensitive completion via one marked `$include` block in
      `~/.inputrc` (also includes `/etc/inputrc`) (1.2)
- [x] One `.bashrc` block `t2-mac-kde: shell-user-tools`, written last, interactive-only; sources grml,
      history and `~/.config/t2-mac-kde/turbo.bash` when readable; foundation nvm block untouched (1.3–1.5)
- [x] `kbus`/`kbde`/`setxkbmap` shim only in Hyprland with `hypr-kbd`; KDE keeps native commands (1.6)
- [x] Dropped from source: Copilot token export, uutils PATH, xfconf/xfce4-terminal, QUARTO_PYTHON block (3.5)
- [x] `bash-completion` via `install_packages(source="ubuntu")`
- [x] Completions for kubectl (+`k`), helm, gh, ax, rc: temp file + `bash -n`, header-marked, unmanaged
      files never replaced, failed/missing providers removed only if ours (4.3, 4.4)
- [x] nvim-simple `70717b4` with five commit-pinned plugins, vendored plug.vim (no master fetch), staged in
      a temp XDG home, verified commits + clean second startup before publishing; foreign config moved to
      `~/.config/nvim.backup-<ts>`; `plugin/debian-hypr-theme.lua` kept in place (2.1–2.5)
- [x] npm globals pnpm/@github/copilot/@openai/codex/ccusage at exact versions under nvm Node from
      `.nvmrc`; checks `npm prefix -g` is the nvm prefix; no `.npmrc` writes (3.1)
- [x] euporie 2.10.4 + ipykernel 7.4.0 via `uv tool install`, kernel import verified (3.2)
- [x] pretty-mermaid skill via pinned `skills@1.8.1`, skipped when `SKILL.md` exists (3.3)
- [x] ax v0.3.1 (GOTOOLCHAIN go1.27.2) with private GOCACHE/GOMODCACHE, only when `go` exists (4.5)
- [x] dev-disk-reclaim: report-only default, `--apply` deletes, sudo/apt/journal branch removed, volumes
      kept unless `--volumes`, `uv cache prune` without `--force`; units installed, timer off by default
      (`DEV_DISK_REPORT_TIMER`) (5.3, 5.4)
- [x] rclone user mounts from `RCLONE_MOUNTS` (empty by default), validated names, resolved rclone path,
      ExecCondition on remote, bounded restarts (5.1, 5.2)
- [x] Unit tests in disposable homes: repeated sourcing, status, array hooks, noninteractive quiet,
      turbo guard, keyboard shim, dir stack bound, completions safety, report-only cleanup, pins

## Deferred / needs owner
- [ ] Safe Chain 1.5.25: upstream installer rewrites shell profiles and can remove nvm; needs a wrapper review
- [ ] Quarto Python env / TinyTeX: depends on application-suite Quarto; not ported yet
- [ ] pretty-mermaid skill repo revision is not pinned (skills CLI resolves the default branch)
- [ ] ax needs Go from application-suite; skipped silently until `go` is on PATH
- [ ] Restore beyond pyinfra `.bashrc`/`.inputrc` backups and the nvim backup dir: not implemented
- [ ] Live check by owner: new Konsole terminal (prompt, history, Up/Down), `nvim` menu/F2/F4, `k <Tab>`
