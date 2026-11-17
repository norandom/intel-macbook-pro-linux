"""Pinned user-local Warpeer from our native Linux build; no sudo or package changes."""
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
    raise RuntimeError("The pinned Warpeer build requires Linux x86-64.")
VERSION = "9ade3d6"
ARCHIVE_SHA256 = "4da7e1ba93b94ab3b1c700b6914085104a14f5e4ebda16f73cb133f13c545966"
BINARY_SHA256 = "fccd0702665650eb1cbce91a4d2a4c2b247c8890d25008a534aa9538aa9298cb"
URL = f"https://github.com/norandom/warpeer/releases/download/desktop-{VERSION}/warpeer-linux-x86_64.tar.gz"
home = Path.home()
opt = home / ".local/opt"
dest = opt / f"warpeer-{VERSION}"
binary = dest / "warpeer"
launcher = home / ".local/bin/warpeer"
if launcher.exists() and not launcher.is_symlink():
    raise RuntimeError(f"Refusing to replace an unmanaged executable: {launcher}")
if launcher.is_symlink() and not str(launcher.readlink()).startswith(str(opt / "warpeer-")):
    raise RuntimeError(f"Refusing to replace an unmanaged symlink: {launcher}")
installed = False
if binary.is_file() and os.access(binary, os.X_OK):
    with binary.open("rb") as stream:
        installed = hashlib.file_digest(stream, "sha256").hexdigest() == BINARY_SHA256
if not installed:
    server.shell(name=f"Warpeer {VERSION}: verified user-local install", commands=f"""set -eu
mkdir -p {quote(str(opt))}
t=$(mktemp -d {quote(str(opt / '.warpeer.XXXXXX'))})
trap 'rm -rf "$t"' EXIT
curl -fsSL --retry 3 --proto '=https' --tlsv1.2 -o "$t/archive.tar.gz" {quote(URL)}
echo '{ARCHIVE_SHA256}  '"$t/archive.tar.gz" | sha256sum -c --quiet
mkdir "$t/payload"
tar --no-same-owner --strip-components=1 -xzf "$t/archive.tar.gz" -C "$t/payload"
echo '{BINARY_SHA256}  '"$t/payload/warpeer" | sha256sum -c --quiet
chmod 755 "$t/payload/warpeer"
# Only replace this exact managed version, after both checksum checks pass.
rm -rf {quote(str(dest))}
mv -T "$t/payload" {quote(str(dest))}
""")
files.link(name="Warpeer command", path=str(launcher), target=str(binary), create_remote_dir=True)
icon = home / ".local/share/icons/hicolor/1024x1024/apps/warpeer.png"
files.put(name="Warpeer icon", src="files/applications/warpeer.png", dest=str(icon),
          mode="644", create_remote_dir=True)
entry = f'''[Desktop Entry]
Type=Application
Name=Warpeer
Comment=Terminal without cloud accounts
Exec="{launcher}" %U
TryExec={launcher}
Icon={icon}
Terminal=false
Categories=System;TerminalEmulator;
StartupNotify=true
'''
files.put(name="Warpeer application menu entry", src=StringIO(entry),
          dest=str(home / ".local/share/applications/warpeer.desktop"), mode="644", create_remote_dir=True)

# Let Warpeer bootstrap the selected shell itself. An exec from Bash's first
# prompt discards the Bash hooks after Warpeer has initialized its protocol.
from manage import fish_shell
from manage.userconfig import setting
from manage.warpeer import startup_shell_config, pinned_input_config, font_config, contrast_config

shell = setting("shell_interactive")
settings = home / ".config/warpeer/settings.toml"
original = settings.read_text() if settings.exists() else ""
updated = font_config(pinned_input_config(startup_shell_config(original, shell)),
                      setting("warpeer_font", "Fixedsys Excelsior"))
updated = contrast_config(updated)
backup = settings.with_name("settings.toml.pre-t2-native-shell")
if settings.exists() and original != updated and not backup.exists():
    files.put(name="Back up Warpeer preferences", src=StringIO(original), dest=str(backup), mode="600")
files.put(name="Warpeer: native shell, pinned input, font and automatic contrast", src=StringIO(updated), dest=str(settings),
          mode="600", create_remote_dir=True)
if shell == "fish":
    files.block(name="Keep Warpeer's shell integration intact", path=str(home / ".bashrc"),
                marker=fish_shell.MARKER, content=fish_shell.BASHRC,
                backup=True, try_prevent_shell_expansion=True)
