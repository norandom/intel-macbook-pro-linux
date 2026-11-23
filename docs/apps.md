# Apps

Three tasks install applications, each with its own route:

| Task | Route |
|---|---|
| `tasks/apps.py` | Ubuntu archive, plus a few pinned upstream binaries into `~/.local/bin` |
| `tasks/vendor_apps.py` | Vendor apt repos with a committed, checksummed key; pinned vendor `.deb`s; pinned tarballs in `~/.local/opt` |
| `tasks/office_apps.py` | LibreOffice from Ubuntu; the Craft suite and OpenIDEA as pinned `.deb`s |

Every download is checked against a sha256 in the repository, and every `.deb` goes through the
package guard ([safety.md](safety.md)). The full inventory, with the reason for each entry, is in
`manage/applications.py`.

## Office and creative

| App | For | Notes |
|---|---|---|
| LibreOffice Writer, Calc | Documents, spreadsheets | Tabbed (ribbon-style) UI by default, German UI pack, de and en-US spelling, Carlito font (metric-compatible with Calibri) |
| WordCraft, GridCraft, DeckCraft | Documents, spreadsheets, slides | Craft suite; layouts follow the programs they replace |
| PdfCraft | PDFs | |
| LightCraft | Photos | Lightroom-style |
| PhotoCraft | Photo editing | Photoshop-style, written in Rust |
| DesignCraft | Page layout | |
| CADCraft | Drawings | |
| Obsidian, Typora | Notes, Markdown | |
| qpdfview, xpdf | PDF viewers | |
| Ristretto | Image viewer | |
| VLC | Video and audio player | The QuickTime Player replacement |
| ffmpeg | Convert, cut and record video and audio (command line) | Ubuntu's build, so hardware encoding through VA-API works |
| Clapper | Video player without FFmpeg | GStreamer; the alternative to VLC, see below |

Clapper is the FFmpeg-free player. It decodes through GStreamer: on the Intel GPU through
VA-API (H.264, HEVC, VP8/VP9; quiet and low power), otherwise in software with openh264
(H.264), libde265 (HEVC), aom (AV1), libvpx, faad (AAC), a52dec (AC-3), libdca (DTS), mpeg2dec
(MPEG-2) and mpg123. MP4, MKV/WebM and MPEG-TS files and HLS/DASH streams play. Without FFmpeg
there is no decoder for E-AC-3 (Dolby Digital Plus), TrueHD, DTS-HD extensions, or Windows Media
audio and video: Clapper reports a missing plugin, and VLC plays those files. `gstreamer1.0-libav`, GStreamer's FFmpeg plugin, is never
installed. VLC and the `ffmpeg` command still use FFmpeg; Clapper doesn't touch it.

The Craft apps are young projects, so expect rough edges. LibreOffice Impress isn't installed;
DeckCraft covers slides. You can change the LibreOffice UI per user in View > User Interface.

If you live in real Excel macros or a heavy Photoshop workflow, these won't cover everything. Run
Windows in virt-manager for those ([developer-tools.md](developer-tools.md#virtual-machines)).

## Browsers

| Browser | Route | Notes |
|---|---|---|
| Vivaldi | Vivaldi's apt repo, sha256-pinned key (replaces the package's own `vivaldi.sources`) | The owner's default browser; the Waybar web button starts it |
| Chromium | XtraDeb PPA, pinned to the Chromium packages only | Comes with `chromedriver` of the same major version |
| Firefox Developer Edition | Mozilla's apt repo, pinned to Developer Edition only | Ubuntu's Snap-transition `firefox` package can't be installed |
| Zen | Pinned tarball in `~/.local/opt` | Updates itself after the first install |

The deploy doesn't pick a default browser for you; set one with `[default_apps]` in the config
(the owner's points http/https/html at `vivaldi-stable.desktop`, see [configuration.md](configuration.md)).

## Communication and everyday

Slack, Discord, Zoom (screen sharing through the Wayland portal), Bitwarden, Remote Desktop
Manager, Rclone UI. Remote desktop client: 1-1 (your own RDP client, pinned `.deb`;
Remmina was removed on request).

## Development

VS Code and Sublime Text (vendor repos), Zed (tarball), Positron and Quarto (`.deb`), OpenIDEA,
Podman Desktop, Meld, edb, heaptrack, and the Intel oneAPI compilers. Terminals: Terminator,
foot, Ghostty, xfce4-terminal (Contour is planned, [backlog](backlog.md)). Classic X apps: Xfe (file manager), NEdit, x3270 and c3270.
TUI tools: atop, posting, lazygit, glow, gdu, trippy, multitail, byobu (tmux with a status
bar and F-key shortcuts), lftp (FTP/SFTP with mirroring and queues), upmd, rc (rustfs-cli). More
CLI tools come from Nix ([nix.md](nix.md)).

## Updates

- Apps from apt repos update with your normal `apt upgrade`.
- Pinned `.deb`s and tarballs update when you bump the pin in `manage/applications.py` or
  `tasks/office_apps.py` and re-run the task. Zen and Discord update themselves; Podman
  Desktop's own update check is turned off.

## Status

```sh
.venv/bin/python -m manage.applications   # what's installed, missing or blocked
```

`tasks/apps.py` also writes `~/.local/state/t2-mac-kde/applications.json`.

## Default apps

Set them per MIME type in your config. The value is a desktop file from `/usr/share/applications`
or `~/.local/share/applications`:

```toml
[default_apps]
"application/pdf" = "ai.storyteller.pdfcraft.desktop"
```

The desktop task applies them with `xdg-mime`. Without this table the system defaults stay.

## Add or remove an app

| You want | Edit |
|---|---|
| An Ubuntu package | add it to `NATIVE` in `manage/applications.py` |
| A vendor `.deb` | add version, URL and sha256 to `VENDOR_DEBS` in `manage/applications.py` |
| A vendor apt repo | add the key and list to `files/vendor-apps/` and an entry to `VENDOR_REPOS` |
| One of the Craft apps less | remove it from `ARTCRAFT` in `tasks/office_apps.py` |
| A CLI tool | `nix_tools_extra` in your config |

The deploy never removes packages, so taking an entry out only stops it from being installed on
new machines; `sudo apt remove` it yourself if you want it gone. Run the tests afterwards
(`.venv/bin/python -m unittest discover -s tests`): some of them, such as
`tests/test_vendor_apps.py`, check these tables. More in
[forking.md](forking.md#adding-or-removing-apps).
