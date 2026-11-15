# Implementation Checklist (desktop-fonts)

User-level port of source `tasks/fonts.py` (a1c09ec). No sudo except the guarded
native package request. Run: `.venv/bin/pyinfra @local tasks/fonts.py [--dry] [--data font_rendering=rgb]`.

## Implemented
- [x] Pins in `manage/fonts.py` (Nerd Fonts v3.5.1 JetBrainsMono/FiraCode, Fixedsys Core cf4b8e9, Fixedsys Excelsior v3.09.10, source sha256s); manifest validation (https, hash, safe names).
- [x] Native packages via `install_packages(PackageRequest(..., source="ubuntu"))`: curl, ca-certificates, xz-utils, fontconfig, xfonts-utils, x11-xserver-utils, fonts-noto-color-emoji, fonts-symbola.
- [x] Nerd Fonts -> `~/.local/share/fonts/{jetbrainsmono,firacode}-nerd/`: download, sha256 check, extract only selected styles, stage `.new`, swap dirs; failure keeps previous family. `.sha256sums` + `.v3.5.1` marker; damaged files trigger reinstall.
- [x] Fixedsys Core / Excelsior -> `~/.local/share/fonts/fixedsys/` (sha256 verified, atomic mv).
- [x] Unchanged state is detected in Python at plan time, so repeat runs and `--dry` schedule nothing for installed fonts (no cache regeneration).
- [x] Core X font index `~/.local/share/fonts-x11core/` (both Fixedsys copies + mkfontscale/mkfontdir, staged, entries verified). Outside fontconfig's dirs to avoid duplicate families.
- [x] Helper `~/.local/bin/hypr-xfonts` (from `files/fonts/hypr-xfonts`): no args; skip exit 0 without `fonts.dir`; 40 x 0.5 s bounded wait; exact path match, `xset +fp` once, `xset fp rehash`; nonblocking flock per DISPLAY in `$XDG_RUNTIME_DIR`; usage exit 2.
- [x] Additive fontconfig fragment `$XDG_CONFIG_HOME/fontconfig/conf.d/60-t2-fonts.conf`: hintslight, AA, grayscale default (rgb optional), monospace = JetBrainsMono Nerd Font, Noto Color Emoji + Symbola weak fallback. `fonts.conf` never touched and loads after conf.d, so KDE/user settings win; overlapping keys there are logged as a warning.
- [x] Tests `tests/test_fonts.py`: manifest, template XML, conflict detection, Nerd install/damage/bad-checksum rollback (stub curl), helper skip/add-once/bounded wait/rehash failure.

## Deferred / owner check
- [ ] Live apply by owner (needs sudo for fonts-symbola) -- agents may not run live deploys.
- [ ] Desktop spec must invoke `~/.local/bin/hypr-xfonts` at session start -- owned by desktop.
- [ ] Visual acceptance (Nerd icons, emoji U+1F600, symbol U+2192, NEdit Fixedsys via `xlsfonts | grep fixedsys`) -- needs a session.
- [ ] Receipt-based restoration/backups -- dropped as ceremony; removal = delete the owned paths above.
- [ ] License files from Nerd archives not extracted (member names unverified offline).
- [ ] Private licensed fonts -- optional/unavailable, never fetched.
