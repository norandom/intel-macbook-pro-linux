"""Pinned user-local Cyberterm 2077 (formerly Warpeer); no sudo or package changes.

The project was renamed at v1.0.0: the release, the executable and the menu entry are
cyberterm2077. Its data stays in the `warpeer` directories (~/.config/warpeer, ~/.warpeer,
~/.local/state/warpeer), so preferences carry over; this task, its config key
(`warpeer_font`) and manage/warpeer.py keep the old name for the same reason.
"""
import hashlib
from io import StringIO
import os
from pathlib import Path
import platform
from shlex import quote

from pyinfra.operations import files, server
from manage.preflight import validate_local_context

validate_local_context()
if platform.machine() != "x86_64":
    raise RuntimeError("The pinned Cyberterm 2077 build requires Linux x86-64.")
NAME = "cyberterm2077"
VERSION = "v1.0.1"
ARCHIVE_SHA256 = "62c501c62012f74f6b7095c586c0c39c51982dddd8a945e229417766ddbffdd7"
BINARY_SHA256 = "79c6075276de6da1e6ecb76b592b6005dc39bb8219ba2dfc7d466e9a58bf84a2"
URL = f"https://github.com/norandom/Cyberterm-2077/releases/download/{VERSION}/{NAME}-linux-x86_64.tar.gz"
home = Path.home()
opt = home / ".local/opt"
dest = opt / f"{NAME}-{VERSION}"
binary = dest / NAME
launcher = home / ".local/bin" / NAME
if launcher.exists() and not launcher.is_symlink():
    raise RuntimeError(f"Refusing to replace an unmanaged executable: {launcher}")
if launcher.is_symlink() and not str(launcher.readlink()).startswith(str(opt / f"{NAME}-")):
    raise RuntimeError(f"Refusing to replace an unmanaged symlink: {launcher}")
installed = False
if binary.is_file() and os.access(binary, os.X_OK):
    with binary.open("rb") as stream:
        installed = hashlib.file_digest(stream, "sha256").hexdigest() == BINARY_SHA256
if not installed:
    server.shell(name=f"Cyberterm 2077 {VERSION}: verified user-local install", commands=f"""set -eu
mkdir -p {quote(str(opt))}
t=$(mktemp -d {quote(str(opt / f'.{NAME}.XXXXXX'))})
trap 'rm -rf "$t"' EXIT
curl -fsSL --retry 3 --proto '=https' --tlsv1.2 -o "$t/archive.tar.gz" {quote(URL)}
echo '{ARCHIVE_SHA256}  '"$t/archive.tar.gz" | sha256sum -c --quiet
mkdir "$t/payload"
tar --no-same-owner --strip-components=1 -xzf "$t/archive.tar.gz" -C "$t/payload"
echo '{BINARY_SHA256}  '"$t/payload/{NAME}" | sha256sum -c --quiet
chmod 755 "$t/payload/{NAME}"
# Only replace this exact managed version, after both checksum checks pass.
rm -rf {quote(str(dest))}
mv -T "$t/payload" {quote(str(dest))}
""")
files.link(name="Cyberterm 2077 command", path=str(launcher), target=str(binary), create_remote_dir=True)
icon = home / f".local/share/icons/hicolor/512x512/apps/{NAME}.png"
files.put(name="Cyberterm 2077 icon", src=f"files/applications/{NAME}.png", dest=str(icon),
          mode="644", create_remote_dir=True)
# StartupWMClass: the window's app id kept the old name (as in the project's own .deb entry).
entry = f'''[Desktop Entry]
Type=Application
Name=Cyberterm 2077
Comment=Task-oriented terminal for Markdown runbooks
Exec="{launcher}" %U
TryExec={launcher}
Icon={icon}
Terminal=false
Categories=System;TerminalEmulator;
StartupNotify=true
StartupWMClass=com.matrixme.warpeer
'''
files.put(name="Cyberterm 2077 application menu entry", src=StringIO(entry),
          dest=str(home / f".local/share/applications/{NAME}.desktop"), mode="644", create_remote_dir=True)

# Retire the pre-rename launcher, menu entry and icon (only our own: a symlink into a managed
# ~/.local/opt/warpeer-* install). The old version directories and all data stay in place.
old_launcher = home / ".local/bin/warpeer"
if old_launcher.is_symlink() and str(old_launcher.readlink()).startswith(str(opt / "warpeer-")):
    files.link(name="Remove the old warpeer command", path=str(old_launcher), present=False)
    for old in (home / ".local/share/applications/warpeer.desktop",
                home / ".local/share/icons/hicolor/1024x1024/apps/warpeer.png"):
        files.file(name=f"Remove {old.name} (renamed)", path=str(old), present=False)

# Let the terminal bootstrap the selected shell itself. An exec from Bash's first
# prompt discards the Bash hooks after it has initialized its protocol.
from manage import fish_shell
from manage.userconfig import setting
from manage.warpeer import startup_shell_config, pinned_input_config, font_config, contrast_config, defaults_config, opaque_config

shell = setting("shell_interactive")
settings = home / ".config/warpeer/settings.toml"   # directory name kept by the rename
original = settings.read_text() if settings.exists() else ""
defaults = (Path(__file__).resolve().parents[1] / "files/warpeer/settings.toml").read_text()
updated = defaults_config(original, defaults)
updated = font_config(pinned_input_config(startup_shell_config(updated, shell)),
                      setting("warpeer_font", "Fixedsys Excelsior"))
updated = opaque_config(contrast_config(updated))
backup = settings.with_name("settings.toml.pre-t2-native-shell")
if settings.exists() and original != updated and not backup.exists():
    files.put(name="Back up Cyberterm 2077 preferences", src=StringIO(original), dest=str(backup), mode="600")
files.put(name="Cyberterm 2077: native shell, pinned input, font, contrast and opaque defaults", src=StringIO(updated), dest=str(settings),
          mode="600", create_remote_dir=True)
if shell == "fish":
    files.block(name="Keep the terminal's shell integration intact", path=str(home / ".bashrc"),
                marker=fish_shell.MARKER, content=fish_shell.BASHRC,
                backup=True, try_prevent_shell_expansion=True)
