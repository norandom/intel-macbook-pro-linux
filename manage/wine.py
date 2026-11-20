"""Wine apps: one prefix ("bottle") per Windows app, under ~/.local/share/wineprefixes/<app>.

A bottle is created once and never deleted or recreated by a deploy, so what an app keeps
inside it (license activation, preferences) survives. Each later Wine app gets its own
bottle through the same helpers; nothing is shared between bottles.
"""
from pathlib import Path
from shlex import quote

PACKAGES = ("wine", "wine64", "wine32:i386", "winetricks", "cabextract", "icoutils")
# Ubuntu does not put wineserver on PATH; winetricks reads WINESERVER.
WINESERVER = "/usr/lib/x86_64-linux-gnu/wine/wineserver"
# Monitor scale 1.6 (the MacBookPro16,1 panel): 96 * 1.6. With xwayland force_zero_scaling
# the app draws at native pixels, so this sets its size without any upscaling blur.
DEFAULT_DPI = 154
# Names Windows apps ask for that a Linux system does not have.
UI_FONT_REPLACEMENTS = {"Segoe UI": "Noto Sans", "Segoe UI Semibold": "Noto Sans SemiBold"}


def prefix(app: str, home: Path | None = None) -> Path:
    return (home or Path.home()) / ".local/share/wineprefixes" / app


def env(bottle: Path) -> str:
    """Shell environment for every Wine call into one bottle. winemenubuilder stays off:
    Wine would otherwise add its own menu entries and MIME associations; the task adds one
    entry itself."""
    return (f"export WINEPREFIX={quote(str(bottle))} WINEARCH=win64 WINEDEBUG=-all "
            f"WINESERVER={WINESERVER} WINEDLLOVERRIDES=winemenubuilder.exe=d")


def _dword(value: int) -> str:
    return f"dword:{value:08x}"


def _reg_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def registry(dpi: int = DEFAULT_DPI, rendering: str = "grayscale", wayland: bool = False,
             replacements: dict[str, str] | None = None) -> str:
    """REGEDIT4 text applied on every deploy: DPI, font smoothing (same choice as the
    desktop's font_rendering), Windows 10, display driver, font name replacements."""
    if not 96 <= dpi <= 480:
        raise ValueError(f"wine dpi out of range: {dpi}")
    if rendering not in ("grayscale", "rgb"):
        raise ValueError(f"font_rendering must be grayscale or rgb: {rendering}")
    smoothing_type = 2 if rendering == "rgb" else 1  # 2 = ClearType, 1 = grayscale
    lines = ["REGEDIT4", "",
             r"[HKEY_CURRENT_USER\Control Panel\Desktop]",
             f'"LogPixels"={_dword(dpi)}',
             '"FontSmoothing"="2"',
             f'"FontSmoothingType"={_dword(smoothing_type)}',
             f'"FontSmoothingGamma"={_dword(1400)}',
             f'"FontSmoothingOrientation"={_dword(1)}',  # RGB, as the panel
             "",
             r"[HKEY_LOCAL_MACHINE\System\CurrentControlSet\Hardware Profiles\Current\Software\Fonts]",
             f'"LogPixels"={_dword(dpi)}',
             "",
             r"[HKEY_CURRENT_USER\Software\Wine]",
             '"Version"="win10"',
             "",
             r"[HKEY_CURRENT_USER\Software\Wine\Drivers]",
             f'"Graphics"={_reg_string("wayland,x11" if wayland else "x11")}',
             "",
             r"[HKEY_CURRENT_USER\Software\Wine\Fonts\Replacements]"]
    for name, target in sorted((UI_FONT_REPLACEMENTS if replacements is None else replacements).items()):
        lines.append(f"{_reg_string(name)}={_reg_string(target)}")
    return "\n".join(lines) + "\n"


def bottle_script(bottle: Path, verbs: tuple[str, ...]) -> str:
    """Create the bottle if missing and add winetricks verbs not yet in its log (each verb
    runs once; winetricks checks the checksums of what it downloads)."""
    lines = ["set -eu", env(bottle),
             'if [ ! -f "$WINEPREFIX/system.reg" ]; then',
             '  mkdir -p "$(dirname "$WINEPREFIX")"',
             # mscoree/mshtml off for the first boot only: no Wine Mono/Gecko download
             # dialog (Ubuntu does not package them; dotnet48 replaces Mono anyway).
             "  WINEDLLOVERRIDES=\"$WINEDLLOVERRIDES;mscoree,mshtml=\" wineboot --init", '  "$WINESERVER" --wait', "fi"]
    for verb in verbs:
        lines += [f'if ! grep -qx {quote(verb)} "$WINEPREFIX/winetricks.log" 2>/dev/null; then',
                  f"  winetricks --unattended {quote(verb)}", '  "$WINESERVER" --wait', "fi"]
    return "\n".join(lines) + "\n"


def installer_script(bottle: Path, url: str, sha256: str, version: str, marker: Path,
                     args: tuple[str, ...], installed_exe: Path) -> str:
    """Download a pinned installer to the user cache, check it, run it unattended in the
    bottle, then record the version (only after the app's executable exists)."""
    cache = Path.home() / ".cache/t2-mac-kde/wine"
    exe = cache / f"{bottle.name}-{version}-installer.exe"
    q = quote
    return "\n".join([
        "set -eu", env(bottle), f"mkdir -p {q(str(cache))}",
        f"if ! echo '{sha256}  '{q(str(exe))} | sha256sum -c --quiet - >/dev/null 2>&1; then",
        f"  curl -fsSL --retry 3 --proto '=https' --tlsv1.2 -o {q(str(exe))}.part {q(url)}",
        f"  echo '{sha256}  '{q(str(exe))}.part | sha256sum -c --quiet - || {{ rm -f {q(str(exe))}.part;"
        f" echo 'Installer checksum mismatch: a new upstream release needs a pin bump' >&2; exit 1; }}",
        f"  mv -f {q(str(exe))}.part {q(str(exe))}", "fi",
        f"wine {q(str(exe))} {' '.join(q(a) for a in args)}", '"$WINESERVER" --wait',
        f"test -f {q(str(installed_exe))}",
        f"echo {q(version)} > {q(str(marker))}", f"rm -f {q(str(exe))}", ""])


def launcher(bottle: Path, exe: Path, before: str = "", extra_env: str = "") -> str:
    """~/.local/bin/<app>: run before (per-launch fixups, e.g. after an in-app update), then the app."""
    return "\n".join(["#!/bin/sh", "# Managed by t2-mac-kde (manage/wine.py).", "set -eu", env(bottle),
                      before.rstrip(), (f"export {extra_env}" if extra_env else ""),
                      f"exec wine {quote(str(exe))} \"$@\"", ""])


def icon_script(exe: Path, icon: Path) -> str:
    """Largest icon from the app's own .exe (the app's artwork stays out of this repo)."""
    q = quote
    return "\n".join([
        "set -eu", f"test -f {q(str(icon))} && exit 0", f"mkdir -p {q(str(icon.parent))}",
        't=$(mktemp -d); trap \'rm -rf "$t"\' EXIT',
        f'wrestool -x -t 14 {q(str(exe))} -o "$t"',
        'icotool -x -o "$t" "$t"/*.ico',
        f'cp "$(ls -S "$t"/*.png | head -1)" {q(str(icon))}',  # the largest file is the largest icon
        ""])


def desktop_entry(name: str, comment: str, launcher_path: Path, icon: Path, categories: str, wm_class: str) -> str:
    return (f"[Desktop Entry]\nType=Application\nName={name}\nComment={comment}\n"
            f'Exec="{launcher_path}"\nTryExec={launcher_path}\nIcon={icon}\nTerminal=false\n'
            f"Categories={categories}\nStartupNotify=true\nStartupWMClass={wm_class}\n")
