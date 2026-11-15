# Implementation Checklist: application-suite

Entry point: `.venv/bin/pyinfra @local tasks/apps.py [--dry]`. Inventory: `manage/applications.py`
(`python -m manage.applications` prints read-only status). Tests: `tests/test_apps.py`.

## Implemented
- [x] Complete source inventory (apps.py lists, base.py tools, release_tools, artcraft_apps,
      client_debs, Obsidian/Bitwarden/Ghostty, terminator/xfe) with one disposition each:
      native / release / delegated / excluded / blocked / backlog (test checks coverage).
- [x] Native Ubuntu packages via `install_packages(PackageRequest(..., source="ubuntu"))`:
      aria2 atop c3270 x3270 gdu gh glow golang-go lazygit meld multitail nedit posting qpdfview
      ristretto rsync rust-coreutils trippy xpdf foot xfce4-terminal terminator ghostty.
      gh and ghostty use Ubuntu's native builds instead of the source vendor repo / forky .deb.
- [x] Foundation-owned CLI tools (git bat fd-find fzf gcc make ripgrep tree unzip neovim htop btop ...)
      are observed, not installed twice; cliphist/x11-xserver-utils/podman-tui delegated.
- [x] Release binaries (zellij upmd kubectl helm k9s ktop bw rc rclone) pinned from source
      group_data, sha256-verified, installed to `~/.local/bin` (user-level, atomic rename,
      exactly-one member check, marker in `~/.local/share/t2-mac-kde/release-tools/`).
      Unmanaged existing binaries are skipped with a warning.
- [x] `~/.local/bin/fd -> /usr/bin/fdfind` only if nothing named fd exists there.
- [x] Source desktop entries: x3270, nedit, hidden foot-server/footclient; terminator.desktop
      (Exec=hypr-term) only when `/usr/local/bin/hypr-term` exists.
- [x] Seed-once `~/.config/htop/htoprc` (an existing file is never overwritten).
- [x] Availability report `$XDG_STATE_HOME/t2-mac-kde/applications.json` (schema_version 1,
      re-probed executables; written only on a real run).
- [x] No vendor repos, no .debs, no purges, no Snap/Flatpak; LibreOffice and Craft suite stay backlog.

## Deferred / needs owner check
- [x] xfe: tasks/xfe.py unpacks the sha256-verified Ubuntu xfe 2.1.1-1 archive into /usr/local
      (apt `Conflicts: im-config` would remove a KDE-base package); wrappers clear ibus variables.
- [ ] chromium / chromium-driver: blocked, Ubuntu only has the Snap transition package.
- [ ] sublime-text, typora, vivaldi-stable, obsidian, bitwarden desktop, quarto, positron, code:
      blocked until a vendor-repo/.deb route is allowed (existing Vivaldi left untouched).
- [ ] Release archives' member layout (esp. `rc`, `upmd`) verified only on the first live run.
- [ ] Terminator config/plugin, Sublime schemes, VS Code themes: owned by coordinated-themes.
- [ ] Live check: launch terminator/remotinator, x3270, nedit, ghostty after the owner-run deploy.
