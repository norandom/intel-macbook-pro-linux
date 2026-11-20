"""Scrivener 3 for Windows in the Wine bottle `scrivener` (tasks/scrivener.py)."""
from pathlib import Path
from shlex import quote

from manage import wine

VERSION = "3.1.6.0"
SHA256 = "b87bc507be913c712276fc736824a7f3f15ade4735f8d64b8681813d0aaf8a77"
URL = "https://scrivener.s3.amazonaws.com/Scrivener-installer.exe"
APP = "scrivener"
WINDOWS_DIR = r"C:\Program Files\Scrivener3"
# BitRock InstallBuilder: no dialogs; Scrivener's own desktop shortcut stays off (it would
# point at a Windows path Linux cannot start).
INSTALLER_ARGS = ("--mode", "unattended", "--unattendedmodeui", "none", "--prefix", WINDOWS_DIR)


def install_dir(bottle: Path) -> Path:
    return bottle / "drive_c/Program Files/Scrivener3"


def fixups(directory: Path) -> str:
    """Run before every start, so they also hold after Scrivener updates itself:
    - texttospeech removed: without SAPI, Scrivener hangs at start enumerating voices
      (speech is not used);
    - Qt's FreeType font engine instead of GDI: proper kerning and sharper text under Wine."""
    d = quote(str(directory))
    return "\n".join([
        f"rm -rf {d}/texttospeech",
        f"conf={d}/qt.conf",
        'if [ -f "$conf" ] && ! grep -q "fontengine=" "$conf"; then',
        "  if grep -q '^WindowsArguments' \"$conf\"; then",
        "    sed -i 's/^\\(WindowsArguments *= *.*\\)$/\\1,fontengine=freetype/' \"$conf\"",
        "  else",
        "    printf '\\n[Platforms]\\nWindowsArguments = fontengine=freetype\\n' >> \"$conf\"",
        "  fi",
        "fi"])


# Modern TrueType hinting (v40, Wine's default elsewhere); cryptbase builtin for the
# license activation helper (Paddle).
EXTRA_ENV = "FREETYPE_PROPERTIES=truetype:interpreter-version=40 WINEDLLOVERRIDES=\"$WINEDLLOVERRIDES;cryptbase=b\""


def launcher(bottle: Path) -> str:
    directory = install_dir(bottle)
    return wine.launcher(bottle, directory / "Scrivener.exe", fixups(directory), EXTRA_ENV)
