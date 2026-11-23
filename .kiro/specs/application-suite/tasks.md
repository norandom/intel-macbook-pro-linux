# Implementation Checklist: application-suite

Entry point: `.venv/bin/pyinfra @local tasks/apps.py [--dry]`. Inventory: `manage/applications.py`
(`python -m manage.applications` prints read-only status). Tests: `tests/test_apps.py`.

## Implemented
- [x] Complete source inventory (apps.py lists, base.py tools, release_tools, artcraft_apps,
      client_debs, Obsidian/Bitwarden/Ghostty, terminator/xfe) with one disposition each:
      native / release / vendor / delegated / excluded / blocked / backlog (test checks coverage).
- [x] Native Ubuntu packages via `install_packages(PackageRequest(..., source="ubuntu"))`:
      aria2 atop c3270 x3270 gdu gh glow golang-go lazygit meld multitail nedit posting qpdfview
      ristretto rsync rust-coreutils trippy xpdf foot xfce4-terminal terminator ghostty edb-debugger heaptrack heaptrack-gui.
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
- [x] No purges, no Snap/Flatpak in tasks/apps.py.
- [x] tasks/vendor_apps.py (owner-approved): sha-pinned keyring repos sublime-text, code (own repo entry
      suppressed via debconf), typora, intel-oneapi icx/icpx, firefox-devedition (Mozilla repo pinned to it), chromium + chromium-driver (XtraDeb PPA pinned to chromium only);
      pinned .debs obsidian, bitwarden, quarto, positron, zoom, slack, discord, rclone-ui, 1-1;
      user tarballs zed, zen, podman-desktop in ~/.local/opt (+ userns AppArmor profiles).
- [x] tasks/office_apps.py: LibreOffice Writer+Calc (de/en-US, Carlito; guarded apt) + Tabbed UI layer
      t2-mac-kde.xcd; ArtCraft suite (7) and OpenIDEA as pinned sha256 .debs via the package guard.

## Deferred / needs owner check
- [x] lftp and byobu from the Ubuntu archive (NATIVE; owner request 2026-11-16).
- [ ] Contour terminal: backlog (docs/backlog.md); not in Ubuntu 26.04, upstream .deb + five palettes later.
- [x] xfe: tasks/xfe.py unpacks the sha256-verified Ubuntu xfe 2.1.1-1 archive into /usr/local
      (apt `Conflicts: im-config` would remove a KDE-base package); wrappers clear ibus variables.
- [ ] vivaldi-stable: still blocked (existing install left untouched).
- [ ] intel-oneapi-vtune: blocked (postinst builds/loads SEP kernel modules; see manage/applications.py).
- [ ] vendor_apps.py not wired into deploy.py yet (after apps); live check of each vendor app, chromedriver.
- [ ] Release archives' member layout (esp. `rc`, `upmd`) verified only on the first live run.
- [ ] Terminator config/plugin, Sublime schemes, VS Code themes: owned by coordinated-themes.
- [ ] office_apps.py not wired into deploy.py yet; live check of Writer/Calc ribbon, craft apps, OpenIDEA.
- [ ] Live check: launch terminator/remotinator, x3270, nedit, ghostty after the owner-run deploy.
