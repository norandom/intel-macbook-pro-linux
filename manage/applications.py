"""Application inventory ported from the source tasks/apps.py (+ desktop.py terminator/xfe).

Source: norandom/hyperland-forky-worker-vm @ a1c09ec3f02a98b7c6a4641f907108a2ad080993
(tasks/apps.py, tasks/base.py, tasks/desktop.py, group_data/all.py).

Every source entry appears exactly once in CATALOG with a disposition:
  native    installed here from the Ubuntu archive (manage.packages guard)
  release   pinned upstream release binary into ~/.local/bin (sha256 verified)
  nix       user Nix profile "t2-tools" (tasks/nix_tools.py; manage/nix_tools.MIGRATED)
  delegated installed by another spec (owner named)
  excluded  intentionally not ported on this laptop
  vendor    official vendor apt repo, pinned vendor .deb or pinned user-level tarball
            (tasks/vendor_apps.py; owner-approved routes)
  blocked   no permitted route yet (vendor apt repo / .deb / Snap-only)
  backlog   deferred by the owner (docs/backlog.md)
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from manage.nix_tools import DEFAULT_TOOLS, MIGRATED, NIX_PREFERRED

SOURCE_REVISION = "a1c09ec3f02a98b7c6a4641f907108a2ad080993"

# id -> (Ubuntu package, executable). Installed by tasks/apps.py.
NATIVE = {
    "aria2": ("aria2", "aria2c"),
    "atop": ("atop", "atop"),
    "c3270": ("c3270", "c3270"),
    "x3270": ("x3270", "x3270"),
    "gdu": ("gdu", "gdu"),
    "gh": ("gh", "gh"),  # source: cli.github.com vendor repo; Ubuntu ships it natively
    "glow": ("glow", "glow"),
    "golang-go": ("golang-go", "go"),
    "lazygit": ("lazygit", "lazygit"),
    "meld": ("meld", "meld"),
    "multitail": ("multitail", "multitail"),
    "nedit": ("nedit", "nedit"),
    "posting": ("posting", "posting"),
    "qpdfview": ("qpdfview", "qpdfview"),
    "ristretto": ("ristretto", "ristretto"),
    "rsync": ("rsync", "rsync"),
    "rust-coreutils": ("rust-coreutils", "coreutils"),
    "trippy": ("trippy", "trip"),
    "xpdf": ("xpdf", "xpdf"),
    "foot": ("foot", "foot"),
    "xfce4-terminal": ("xfce4-terminal", "xfce4-terminal"),
    # source desktop.py auxiliary apps (hyprland-core profile)
    "terminator": ("terminator", "terminator"),
    # source: Debian forky .deb from mkasberg/ghostty-ubuntu; Ubuntu 26.04 ships it natively
    "ghostty": ("ghostty", "ghostty"),
    # GUI dev tools (owner request 2026-11-16). Launch targets under them; attaching to a
    # running process needs ptrace_scope 0, which is not changed here.
    "edb-debugger": ("edb-debugger", "edb"),
    "heaptrack": ("heaptrack", "heaptrack"),
    "heaptrack-gui": ("heaptrack-gui", "heaptrack_gui"),
    # Media player (owner request 2026-11-16; Ubuntu .deb, not a snap)
    "vlc": ("vlc", "vlc"),
    # Video player for network shares (owner request 2026-11-23): on the sshfs filer an unread MKV
    # starts in ~2 s, VLC took over a minute (its MKV demuxer seeks hundreds of times).
    "mpv": ("mpv", "mpv"),
    # KDE player on top of mpv (same fast start); default for video via config [default_apps]
    "haruna": ("haruna", "haruna"),
    # SFTP shares as a local folder (owner request 2026-11-23: media streaming from the filer;
    # kernel page cache + offset reads, so players can seek, unlike an rclone stream)
    "sshfs": ("sshfs", "sshfs"),
    # apt rather than Nix: Ubuntu's build finds the system VA-API drivers (Intel/AMD hardware encode)
    "ffmpeg": ("ffmpeg", "ffmpeg"),
    # FFmpeg-free video player (owner request 2026-11-16): GStreamer, see GSTREAMER below
    "clapper": ("clapper", "clapper"),
    # File transfer (FTP/SFTP/mirror) and a terminal multiplexer front end (owner request 2026-11-16)
    "lftp": ("lftp", "lftp"),
    "byobu": ("byobu", "byobu"),
    # rustup from Ubuntu, not Nix: it leaves rust-lang.org toolchains as built (system glibc), so
    # build scripts and proc-macros run against the same glibc the system linker uses.
    "rustup": ("rustup", "rustup"),
    # KDE calendar (owner request 2026-11-23); Google Calendar via the Google Groupware resource.
    # Akonadi + kdepim-runtime come as dependencies. Mail is Penguin Mail (VENDOR_DEBS).
    "korganizer": ("korganizer", "korganizer"),
    # E-book library and reader (owner request 2026-11-23)
    "calibre": ("calibre", "calibre"),
}
# KOrganizer plugins (e.g. holiday and date plugins); only a recommend, the guard skips those
KDEPIM_ADDONS = ("kdepim-addons",)

# GStreamer decoders for Clapper without FFmpeg (never gstreamer1.0-libav, which is FFmpeg):
#   plugins-bad: openh264 (H.264), de265 (HEVC), aom (AV1), faad (AAC), MPEG-TS, HLS/DASH
#   ugly: a52dec (AC-3 / Dolby Digital), mpeg2dec (MPEG-2, DVD), DVD subtitles and LPCM
#   vaapi: hardware decoding on the Intel GPU (H.264, HEVC, VP8/VP9): quiet and low power
# plugins-base/-good (MP4, MKV/WebM, VP8/VP9, MP3, Opus, FLAC) are already there with KDE.
GSTREAMER = ("gstreamer1.0-plugins-bad", "gstreamer1.0-plugins-ugly", "gstreamer1.0-vaapi")
NEVER = ("gstreamer1.0-libav",)

# name -> (version, url, sha256), verbatim from source group_data/all.py release_tools.
# Only tools nixpkgs lacks (upmd; rc = rustfs-cli, nixpkgs "rc" is the Plan 9 shell; leaves is
# not in nixos-26.05).
RELEASE_TOOLS = {
    "upmd": ("0.2.7", "https://github.com/rezigned/upmd/releases/download/v0.2.7/upmd-x86_64-unknown-linux-gnu.tar.xz",
             "101336d7a8f4648a3bf894d5636875f1df3d219719d470096c562e0cf4d6b9aa"),
    "rc": ("0.1.36", "https://github.com/rustfs/cli/releases/download/v0.1.36/rustfs-cli-linux-amd64-v0.1.36.tar.gz",
           "4a8128911ccad4e7b481f26635a4cfd1ec064412210526e57ad2c748d356f3b7"),
    # Text-mode disk usage map (owner request 2026-11-23); static musl binary, MPL-2.0.
    "leaves": ("0.2.0", "https://github.com/patonw/leaves/releases/download/v0.2.0-cross/leaves-v0.2.0-cross-x86_64-linux-musl",
               "56ce36eab284b0bfc3ca554cddf21ebc137c1da41f9784e7e9dfe905f8cc3839"),
}
# Pins of tools Nix provides now (manage/nix_tools.MIGRATED). tasks/apps.py installs one again
# only when its attribute is taken out of config nix_tools (spec nix-user-tools req 4.2).
RELEASE_FALLBACK = {
    "zellij": ("0.45.1", "https://github.com/zellij-org/zellij/releases/download/v0.45.1/zellij-x86_64-unknown-linux-musl.tar.gz",
               "40bcc2e03f5d5ae8e054e39f676081fe12ab70871506996ba595834c3718eefc"),
    "kubectl": ("1.37.1", "https://dl.k8s.io/release/v1.37.1/bin/linux/amd64/kubectl",
                "65691ff77eb6fa44c908b77a1082c9f092c3b9733b5cefabec0d1104890e21a8"),
    "helm": ("4.3.0", "https://get.helm.sh/helm-v4.3.0-linux-amd64.tar.gz",
             "86584a54def73570558f66f5111cc53dfed56689637ae32c1201205d494f54fb"),
    "k9s": ("0.51.0", "https://github.com/derailed/k9s/releases/download/v0.51.0/k9s_Linux_amd64.tar.gz",
            "c3752ad51a5a4015a113819c4eeb6e55a4d0e4b8e652494797532f6fc8161dd7"),
    "ktop": ("0.5.3", "https://github.com/vladimirvivien/ktop/releases/download/v0.5.3/ktop_v0.5.3_linux_amd64.tar.gz",
             "f8104e5d09bb764da014ba87e5f75c73f55a26b907e9699f43176848a33dbea6"),
    "bw": ("2026.9.1", "https://github.com/bitwarden/clients/releases/download/cli-v2026.9.1/bw-linux-2026.9.1.zip",
           "84289eaf59d691f04242605112f21b00e8dba65acdedbc60dde001a2860f2097"),
    "rclone": ("1.75.2", "https://github.com/rclone/rclone/releases/download/v1.75.2/rclone-v1.75.2-linux-amd64.zip",
               "349ac8fba6ff65d6247043f1750cdcb518ec5d500ef91463a10d37c0ccdf3702"),
}

# --- Vendor routes (tasks/vendor_apps.py) -----------------------------------------
# Official apt repos: id -> (list/keyring name, apt packages, executable, key sha256).
# Key fingerprints (gpg --show-keys):
#   sublime-text 1EDDE2CDFC025D17F6DA9EC0ADAE6AD28A8F901A, 1B64279675A4299DCFC70858CA464A9A222D23D0,
#                EBC733B78AAB352DC773BF857FE2FA12CF6E38F2 (current signer)
#   code         BC528686B50D79E339D3721CEB3E94ADBE1229CF (Microsoft Release signing)
#   typora       4AC441BE68B4ADAB7439FBF9BA300B7755AFCFAE (Typora linux packages)
#   xtradeb      5301FA4FD93244FBC6F6149982BB6851C64F6880 (Launchpad PPA for xtradeb)
#   mozilla      35BAA0B33E9EB396F59CA838C0BA5CE6DC6315A3 (Mozilla's documented apt signer)
#   vivaldi      8D1FA52AEF58A09D889DD4221256C34716BD9233 (Vivaldi Package Composer KEY11, signs
#                the stable Release; the file also carries DE785BB96CE4A58D79377D3574CB4872D93D8726)
#   intel-oneapi E9BF0AFC46D6E8B7DA5882F1BAC6F0C353D04109 (Intel Software Development Products,
#                current signer; the file also carries Intel's four expired predecessor keys)
VENDOR_REPOS = {
    "sublime-text": ("sublime-text", ("sublime-text",), "subl",
                     "0c1b881841c723766c142ca122f3778016dc62d16f0011ccc36b6f8e5a836b28"),
    "code": ("code", ("code",), "code",
             "098f10efd65c0d0a856a980144b5f37c05374eaa575a208d46913fd8f7eae951"),
    "typora": ("typora", ("typora",), "typora",
               "06bbbb3681896a3961dd8630594a92773e8f1aa750aa2e5398fe536e2529dd2e"),
    "chromium": ("xtradeb", ("chromium", "chromium-driver"), "chromium",
                 "cfce8900b216d10492cd1383ff43c8fcb3343a7fe9413fbae5121958b9a80a3e"),
    # icx/icpx; not on PATH (no setvars.sh, no CC/CXX), so the probe is the absolute path.
    "intel-oneapi": ("intel-oneapi", ("intel-oneapi-compiler-dpcpp-cpp",), "/opt/intel/oneapi/compiler/latest/bin/icx",
                     "b64d30657bf1ba91aec0f932910419698047c9ab6387cbbe52430dc59bcf6d86"),
    # The one Firefox here (web dev); Ubuntu's snap-transitional firefox is pinned to -1.
    # The owner's default browser (also x-www-browser); only vivaldi-stable is installed from it.
    "vivaldi-stable": ("vivaldi", ("vivaldi-stable",), "vivaldi-stable",
                "63077a16d31c9acaaf425770ba397f78764089f39dccd1f05504f7af692912b5"),
    "firefox-devedition": ("mozilla", ("firefox-devedition", "firefox-devedition-l10n-de"), "firefox-devedition",
                           "a22e1a7885381e4005b61884a5205892c39d15f5c262555e38b4fe5402ca8895"),
}
# Pinned vendor .debs: id -> (dpkg package, dpkg Version, url, sha256, executable).
VENDOR_DEBS = {
    # Mail + calendar with Google sign-in through GNOME Online Accounts (owner request 2026-11-23).
    # GTK 4 / libadwaita, GPL-3.0. The .deb also brings its own signed apt repo
    # (c9dev.github.io/penguin-mail, key FE3C3B6E699AF939DC4670DCF3A853035C3E2B8E = the published one).
    "penguin-mail": ("penguin-mail", "1.0.12",
                     "https://github.com/c9dev/penguin-mail/releases/download/v1.0.12/penguin-mail_1.0.12_amd64.deb",
                     "395589a2982f1b99498fbab791f70a4bf34e5c19ca2727cc78e63ebf5b6672ce", "penguin-mail"),
    "obsidian": ("obsidian", "1.15.1",
                 "https://github.com/obsidianmd/obsidian-releases/releases/download/v1.15.1/obsidian_1.15.1_amd64.deb",
                 "f77b6dfc8c040214f2febad2b1b9b051b6a838a47b0f4fb90a31cfcb79b8fcec", "obsidian"),
    "bitwarden": ("bitwarden", "2026.10.4",
                  "https://github.com/bitwarden/clients/releases/download/desktop-v2026.10.4/Bitwarden-2026.10.4-amd64.deb",
                  "a45a34a20a9d5becbb1c710851717583ad578597d10fbd2bd57fe597f7625f41", "bitwarden"),
    "quarto": ("quarto", "1.11.9",
               "https://github.com/quarto-dev/quarto-cli/releases/download/v1.11.9/quarto-1.11.9-linux-amd64.deb",
               "64078d1623d9ab89da766591f3410a0756f3737a37efb0897c7e84b863bf092a", "quarto"),
    "positron": ("positron", "2026.11.1+4-1794024154",
                 "https://cdn.posit.co/positron/releases/deb/x86_64/Positron-2026.11.1-4-x64.deb",
                 "3569815ed54083add81a7856f81b33a2d64b3c8e349e2b0cff8154d8fbf29106", "positron"),
    "zoom": ("zoom", "7.2.5.6661", "https://cdn.zoom.us/prod/7.2.5.6661/zoom_amd64.deb",
             "5cd7b9f1e6dc7226a44193df23d0664790496e8267f26152b0cbbd5888025444", "zoom"),
    "slack": ("slack-desktop", "4.53.287",
              "https://downloads.slack-edge.com/desktop-releases/linux/x64/4.53.287/slack-desktop-4.53.287-amd64.deb",
              "c2057f221e41275b7eadc5b658edc00289466b6fb55c912c5894831f6900f969", "slack"),
    "discord": ("discord", "1.0.169", "https://dl.discordapp.net/apps/linux/1.0.169/discord-1.0.169.deb",
                "64d39ef66390149c09ec7d20759a2e4aa0b93efc071d073e3e72155eb86639df", "discord"),
    # 1-1: the owner's own RDP client (norandom/1-1); pre-release, Tauri on system WebKitGTK.
    "1-1": ("1-1", "0.1.0-beta.1",
            "https://github.com/norandom/1-1/releases/download/v0.1.0-beta.1/1-1_0.1.0-beta.1_amd64.deb",
            "31997e17b572d405caba1daf43e06ebb42746db64770f8cf26525b8ba92dfbd8", "rdp-client"),
    # Diffcore: semantic diff / review app for large (agent-made) changes (owner request 2026-11-23).
    # Tauri on the system WebKitGTK, no maintainer scripts. The repo has no license file.
    "diffcore": ("diffcore", "0.5.16",
                 "https://github.com/jamesaphoenix/diff-core/releases/download/v0.5.16/Diffcore_0.5.16_amd64.deb",
                 "fa56ab3e7cf3956c8a86fb55a55f4fa108c10b33c3aade92d36794d26475fd80", "diffcore-tauri"),
    # Mindwtr: GTD to-do app, AGPL-3.0, no account (owner request 2026-11-23). Tauri; its
    # libappindicator3-1 dependency is met by Ubuntu's Ayatana library (Provides), nothing removed.
    "mindwtr": ("mindwtr", "1.3.9",
                "https://github.com/dongdongbh/Mindwtr/releases/download/v1.3.9/mindwtr_1.3.9_amd64.deb",
                "bd0dea355e526855ec6c419dd557fe77fc7244132c16346fa8ab3bcd4e094f7b", "mindwtr"),
    # Fedistar: multi-column Fediverse client (owner request 2026-11-23; their Akkoma instance).
    # Tauri on the system WebKitGTK, GPL-3.0, no maintainer scripts.
    "fedistar": ("fedistar", "1.13.3", "https://github.com/h3poteto/fedistar/releases/download/v1.13.3/fedistar_1.13.3_amd64.deb",
                 "66afefafc7c19d6a9d26ac946c5cf502d99c48f22fac39799c2c0549bc5f1e6f", "fedistar"),
    # witr: "why is this running" - traces a process, port or file to what started it, CLI + TUI
    # (owner request 2026-11-23). Apache-2.0, one static binary + man page, no maintainer scripts.
    "witr": ("witr", "0.3.4", "https://github.com/pranshuparmar/witr/releases/download/v0.3.4/witr-0.3.4-linux-amd64.deb",
             "fa72d5fc255c992c18eb42dabf314eb26ed7590eb39be2c9cd37bb3e2c1cf61c", "witr"),
    "rclone-ui": ("rclone-ui", "3.7.5", "https://github.com/rclone-ui/rclone-ui/releases/download/v3.7.5/Rclone.UI_amd64.deb",
                  "9abf7db50839350fe336710574232197b87be9204036f94390de458b59ab9faf", "Rclone UI"),
}
# Pinned user-level tarballs (~/.local/opt/<id>-<version>): id -> (version, url, sha256, executable).
VENDOR_TARBALLS = {
    "zed": ("1.28.1", "https://github.com/zed-industries/zed/releases/download/v1.28.1/zed-linux-x86_64.tar.gz",
            "9c3fc4cbe533e72c8d0e864a62be2b88d69cc44b9f52cd25d4c21d054dda3742", "zed"),
    "zen": ("1.24.2b", "https://github.com/zen-browser/desktop/releases/download/1.24.2b/zen.linux-x86_64.tar.xz",
            "bcf7e43160ecfe5f29953ed2a984e7a8028a58f2ec0e3114d36bb904d5f5ce80", "zen"),
    # Telegram Desktop, the official build (not in Ubuntu 26.04; owner request 2026-11-23).
    # Its own updater keeps it current in place, so the pin only matters for the first install.
    "telegram": ("7.4.4", "https://github.com/telegramdesktop/tdesktop/releases/download/v7.4.4/td-setup-linux-x64-7.4.4.tar.xz",
                 "607d77344a332268df1ab0c3c9b5adb70a6204e5f78cb668ab3fa58245c0888e", "telegram"),
    # Mendeley Reference Manager (owner request 2026-11-23; replaces the frozen Mendeley Desktop).
    # Electron AppImage, unpacked; it can't update itself that way, so bump the pin by hand.
    # Mendeley publishes no checksum: the sha256 is of the official file fetched 2026-11-23.
    "mendeley": ("2.151.0", "https://static.mendeley.com/bin/desktop/mendeley-reference-manager-2.151.0-x86_64.AppImage",
                 "507e51d2c3f9753b0be63c90a5eea400f67d1b5a4f05ea6c1fdc215447435a33", "mendeley"),
    # Xcode replacement (SwiftPM iOS builds). An AppImage: unpacked once, so no libfuse2 needed.
    "xtool": ("1.24.0", "https://github.com/xtool-org/xtool/releases/download/1.24.0/xtool-x86_64.AppImage",
              "dbfd9d7216f077c84c171b688c4173c37c23ca76bf7fd185d1a9ae8a53dab59f", "xtool"),
}
# System-wide release binaries that need a file capability: id -> (version, url, sha256, caps).
# Root-owned in /usr/local/bin, so the account cannot swap the binary that holds the capability.
SYSTEM_BINARIES = {
    # Traceroute TUI (owner request 2026-11-23): per-hop stats, ASN/geo, ECMP, MPLS. Raw sockets,
    # so cap_net_raw like Ubuntu's trippy. nixos-26.05 has only 0.23.0. Apache-2.0, static musl.
    "ttl": ("0.26.0", "https://github.com/lance0/ttl/releases/download/v0.26.0/ttl-x86_64-unknown-linux-musl.tar.gz",
            "3c8dcd373f8555d41010b7a376a201c55a4d009c62720722f944ad2e1431a587", "cap_net_raw=ep"),
}
_VENDOR_OWNER = "tasks/vendor_apps.py"

_FOUNDATION = "local-system-foundation (tasks/tools.py)"
_OFFICE = "tasks/office_apps.py"
_LIBREOFFICE = "Ubuntu archive via the package guard; Tabbed UI admin layer t2-mac-kde.xcd"
_CRAFT = "pinned storytold GitHub .deb, sha256 + package guard"
_VENDOR = "vendor apt repo / .deb route not permitted by the application-suite spec yet"
_REPO = "official vendor apt repo, sha256-pinned signing key"
_DEB = "pinned vendor .deb (sha256), guarded install"

# id -> (disposition, owner, executable or None, reason)
OTHER = {
    # foundation CLI list (installed there, observed here)
    **{p: ("delegated", _FOUNDATION, exe, None) for p, exe in (
        ("git", "git"), ("bat", "batcat"), ("fd-find", "fdfind"), ("fzf", "fzf"), ("gcc", "gcc"),
        ("make", "make"), ("ripgrep", "rg"), ("tree", "tree"), ("unzip", "unzip"), ("neovim", "nvim"),
        ("curl", "curl"), ("ca-certificates", None), ("jq", "jq"), ("htop", "htop"), ("btop", "btop"))},
    "cliphist": ("delegated", "hyprland-desktop", "cliphist", None),
    "x11-xserver-utils": ("delegated", "desktop-fonts", "xset", None),
    "podman-tui": ("excluded", "containers", "podman-tui",
                   "Podman replaced by Docker Engine (owner 2026-11-25); lazydocker comes from Nix"),
    "dbus-user-session": ("delegated", "hyprland-desktop", None, None),
    "systemd-zram-generator": ("delegated", "laptop-resource-policy", None, None),
    "earlyoom": ("delegated", "laptop-resource-policy", "earlyoom", None),
    "nodejs": ("excluded", "shell-user-tools", "node", "system Node replaced by user nvm"),
    "npm": ("excluded", "shell-user-tools", "npm", "system npm replaced by user nvm"),
    "sudo": ("excluded", "system", "sudo", "already part of the Ubuntu install"),
    "qemu-guest-agent": ("excluded", "none", None, "VM-only; this is a laptop"),
    "littlesnitch": ("excluded", "none", None, "source purge-only entry; not ported"),
    "contour": ("backlog", "application-suite", "contour",
                "owner wants it later (2026-11-16); not in Ubuntu 26.04: upstream .deb, pinned + sha256"),
    "xfe": ("delegated", "tasks/xfe.py", "xfe",
            "Ubuntu xfe 2.1.1-1 unpacked to /usr/local (its Conflicts: im-config would remove a KDE-base package)"),
    "chromium": ("vendor", _VENDOR_OWNER, "chromium", "XtraDeb PPA, pinned to chromium packages only"),
    "chromium-driver": ("vendor", _VENDOR_OWNER, "chromedriver", "XtraDeb PPA, installed with chromium"),
    "sublime-text": ("vendor", _VENDOR_OWNER, "subl", _REPO + " (stable channel)"),
    "typora": ("vendor", _VENDOR_OWNER, "typora", _REPO),
    "vivaldi-stable": ("vendor", _VENDOR_OWNER, "vivaldi-stable", _REPO + " (replaces the package's own vivaldi.sources)"),
    "obsidian": ("vendor", _VENDOR_OWNER, "obsidian", _DEB),
    "penguin-mail": ("vendor", _VENDOR_OWNER, "penguin-mail", _DEB + " (GitHub; then its own signed apt repo)"),
    "bitwarden": ("vendor", _VENDOR_OWNER, "bitwarden", _DEB + " (desktop-v release)"),
    "quarto": ("vendor", _VENDOR_OWNER, "quarto", _DEB),
    "positron": ("vendor", _VENDOR_OWNER, "positron", _DEB + " (Posit CDN)"),
    "code": ("vendor", _VENDOR_OWNER, "code", _REPO + " (Microsoft; package's own repo entry suppressed)"),
    "1-1": ("vendor", _VENDOR_OWNER, "rdp-client", _DEB + " (owner's own RDP client, norandom/1-1)"),
    "intel-oneapi": ("vendor", _VENDOR_OWNER, "/opt/intel/oneapi/compiler/latest/bin/icx",
                     _REPO + " (icx/icpx; Intel EULA, no key)"),
    "zoom": ("vendor", _VENDOR_OWNER, "zoom", _DEB + " (Wayland portal sharing on)"),
    "slack": ("vendor", _VENDOR_OWNER, "slack", _DEB + " (its cron repo-add disabled)"),
    "discord": ("vendor", _VENDOR_OWNER, "discord", _DEB + " (host self-updates in ~/.config/discord)"),
    "firefox-devedition": ("vendor", _VENDOR_OWNER, "firefox-devedition",
                           _REPO + " (Mozilla; pinned to Developer Edition only; not the default browser)"),
    "diffcore": ("vendor", _VENDOR_OWNER, "diffcore-tauri", _DEB + " (jamesaphoenix/diff-core; desktop app only, no CLI)"),
    "mindwtr": ("vendor", _VENDOR_OWNER, "mindwtr", _DEB + " (dongdongbh/Mindwtr; sha256 also in its SHA256SUMS)"),
    "ttl": ("vendor", _VENDOR_OWNER, "ttl", "pinned GitHub release (sha256, also in its SHA256SUMS), "
                                            "/usr/local/bin with cap_net_raw"),
    "fedistar": ("vendor", _VENDOR_OWNER, "fedistar", _DEB + " (h3poteto/fedistar; Mastodon/Pleroma/Akkoma client)"),
    "witr": ("vendor", _VENDOR_OWNER, "witr", _DEB + " (pranshuparmar/witr; sha256 also in its SHA256SUMS)"),
    "rclone-ui": ("vendor", _VENDOR_OWNER, "Rclone UI", _DEB + " (Tauri, system WebKitGTK; point it at Nix rclone)"),
    # Its postinst builds and insmods the SEP sampling drivers and installs a boot script
    # (kernel boundary); VTune 2026.6 HW sampling also does not support this i9-9980HK.
    "intel-oneapi-vtune": ("blocked", "application-suite", None,
                           "postinst builds/loads SEP kernel modules + boot script; user-mode sampling needs "
                           "ptrace_scope 0; HW sampling unsupported on this CPU"),
    **{t: ("vendor", _VENDOR_OWNER, v[3], "pinned upstream tarball (sha256) in ~/.local/opt")
       for t, v in VENDOR_TARBALLS.items()},
    "libreoffice-calc": ("delegated", _OFFICE, "localc", _LIBREOFFICE),
    "libreoffice-writer": ("delegated", _OFFICE, "lowriter", _LIBREOFFICE),
    **{p: ("delegated", _OFFICE, None, _LIBREOFFICE) for p in (
        "libreoffice-gtk3", "libreoffice-l10n-de",
        "fonts-crosextra-carlito", "hunspell-de-de", "hunspell-en-us", "hyphen-de", "hyphen-en-us",
        "mythes-de", "mythes-en-us")},
    **{p: ("delegated", _OFFICE, p, _CRAFT) for p in (
        "pdfcraft", "designcraft", "gridcraft", "lightcraft", "photocraft", "wordcraft", "deckcraft", "cadcraft")},
    "openidea": ("delegated", _OFFICE, "openidea", "pinned l0ng-ai/openidea GitHub .deb (package open-idea), "
                 "sha256 + package guard"),
}


def release_tools(nix_attrs=DEFAULT_TOOLS) -> dict[str, tuple[str, str, str]]:
    """Release pins tasks/apps.py installs: RELEASE_TOOLS + fallbacks whose Nix attribute is off."""
    return {**RELEASE_TOOLS, **{n: pin for n, pin in RELEASE_FALLBACK.items() if MIGRATED[n] not in nix_attrs}}


def catalog(nix_attrs=DEFAULT_TOOLS) -> dict[str, tuple[str, str, str | None, str | None]]:
    """id -> (disposition, owner, executable, reason) for every source entry."""
    entries = {i: ("native", "application-suite", exe, None) for i, (_, exe) in NATIVE.items()}
    entries.update({n: ("release", "application-suite", n, None) for n in release_tools(nix_attrs)})
    overlap = set(entries) & set(OTHER)
    if overlap:
        raise RuntimeError(f"Application ids owned twice: {sorted(overlap)}")
    entries.update(OTHER)
    for app_id, attr in MIGRATED.items():
        if attr in nix_attrs:
            entries[app_id] = ("nix", "tasks/nix_tools.py", app_id, f"nixpkgs {attr} (was a pinned release binary)")
    return entries


def native_packages() -> tuple[str, ...]:
    return tuple(pkg for pkg, _ in NATIVE.values()) + GSTREAMER + KDEPIM_ADDONS


def _dpkg_version(package: str) -> str | None:
    try:
        out = subprocess.run(["dpkg-query", "-W", "-f=${db:Status-Status} ${Version}", package],
                             capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    status, _, version = out.stdout.partition(" ")
    return version if out.returncode == 0 and status == "installed" else None


def needs_pinned_deb(package: str, version: str) -> bool:
    """A pinned .deb installs when the package is missing or older; a newer one (e.g. the
    owner's own build) is kept: apt would refuse the downgrade and fail the batch."""
    installed = _dpkg_version(package)
    if not installed:
        return True
    return subprocess.run(["dpkg", "--compare-versions", installed, "lt", version]).returncode == 0


def observe(home: str | None = None, nix_attrs=DEFAULT_TOOLS) -> list[dict]:
    """Read-only availability probe (Nix profile, ~/.local/bin, then PATH: the session order)."""
    home = home or os.path.expanduser("~")
    path = os.pathsep.join((f"{home}/.nix-profile/bin", f"{home}/.local/bin", os.environ.get("PATH", "/usr/bin:/bin")))
    pins = release_tools(nix_attrs)
    report = []
    for app_id, (disposition, owner, exe, reason) in sorted(catalog(nix_attrs).items()):
        resolved = shutil.which(exe, path=path) if exe else None
        version = None
        if disposition == "native":
            version = _dpkg_version(NATIVE[app_id][0])
        elif disposition == "release":
            version = pins[app_id][0] if resolved else None
        elif app_id in VENDOR_DEBS:
            version = _dpkg_version(VENDOR_DEBS[app_id][0])
        elif app_id in VENDOR_TARBALLS:
            version = VENDOR_TARBALLS[app_id][0] if resolved else None
        elif disposition == "vendor":
            version = _dpkg_version(VENDOR_REPOS[app_id][1][0] if app_id in VENDOR_REPOS else app_id)
        report.append({
            "id": app_id, "owner": owner, "disposition": disposition,
            "selected": disposition in ("native", "release", "vendor", "nix"),
            "installed_version": version, "executable": resolved or exe,
            "available": bool(resolved), "reason": reason,
            "nix_preferred": NIX_PREFERRED.get(app_id) in nix_attrs,
        })
    return report


def report_path(home: str | None = None) -> Path:
    home = home or os.path.expanduser("~")
    state = os.environ.get("XDG_STATE_HOME") or f"{home}/.local/state"
    return Path(state) / "t2-mac-kde" / "applications.json"


def write_report(home: str | None = None, nix_attrs=DEFAULT_TOOLS) -> Path:
    """Write $XDG_STATE_HOME/t2-mac-kde/applications.json (schema_version 1) atomically."""
    target = report_path(home)
    target.parent.mkdir(parents=True, exist_ok=True)
    data = {"schema_version": 1, "source_revision": SOURCE_REVISION,
            "entries": {e["id"]: e for e in observe(home, nix_attrs)}}
    tmp = target.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, target)
    return target


if __name__ == "__main__":  # quick read-only status: python -m manage.applications
    for e in observe():
        state = "ok" if e["available"] else ("MISSING" if e["selected"] else "-")
        nix = " (Nix preferred in PATH)" if e["nix_preferred"] else ""
        print(f"{e['id']:24} {e['disposition']:9} {state:8} {e['reason'] or e['owner']}{nix}")
