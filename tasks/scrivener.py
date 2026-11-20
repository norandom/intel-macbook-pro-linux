"""Scrivener 3 (Windows build) in its own Wine bottle: ~/.local/share/wineprefixes/scrivener.

Opt-in (config `scrivener = true`): Wine from the Ubuntu archive (guarded apt install,
the only sudo step), then as the user: the bottle with corefonts and .NET 4.8 (license
activation needs it; first run ~10 min), the pinned Scrivener installer (sha256-checked,
unattended), a `scrivener` command and an Office menu entry. Speech is left out (see
manage/scrivener.py). The license key is entered once in Scrivener's own dialog and stays
in the bottle; a deploy never deletes or recreates the bottle. Pins: manage/scrivener.py.
"""
from io import StringIO
from pathlib import Path
from shlex import quote

from pyinfra.operations import files, server
from manage import scrivener, wine
from manage.packages import PackageRequest, install_packages
from manage.preflight import validate_local_context
from manage.userconfig import setting

validate_local_context()
if setting("scrivener", False):
    home = Path.home()
    bottle = wine.prefix(scrivener.APP, home)
    directory = scrivener.install_dir(bottle)
    marker = bottle / ".t2-mac-kde-version"   # the Scrivener version this task installed
    install_packages(PackageRequest(packages=wine.PACKAGES))
    server.shell(name="Scrivener bottle: Wine prefix, corefonts, .NET 4.8 (first run ~10 min)",
                 commands=[wine.bottle_script(bottle, ("corefonts", "dotnet48"))], _shell_executable="bash")
    reg = bottle / "t2-mac-kde.reg"
    put = files.put(name="Scrivener bottle: DPI, font smoothing, Windows 10, display driver",
                    src=StringIO(wine.registry(int(setting("scrivener_dpi", wine.DEFAULT_DPI)),
                                               setting("font_rendering", "grayscale"),
                                               bool(setting("scrivener_wayland", False)))),
                    dest=str(reg), mode="644", create_remote_dir=True)
    server.shell(name="Scrivener bottle: apply registry settings", _if=put.did_change, _shell_executable="bash",
                 commands=[f'set -eu\n{wine.env(bottle)}\nwine regedit /S "$(winepath -w {quote(str(reg))})"\n'
                           '"$WINESERVER" --wait'])
    if not (marker.is_file() and marker.read_text().strip() == scrivener.VERSION):
        server.shell(name=f"Scrivener {scrivener.VERSION}: verified unattended install", _shell_executable="bash",
                     commands=[wine.installer_script(bottle, scrivener.URL, scrivener.SHA256, scrivener.VERSION,
                                                     marker, scrivener.INSTALLER_ARGS, directory / "Scrivener.exe")])
    launcher = home / ".local/bin" / scrivener.APP
    files.put(name="Scrivener command", src=StringIO(scrivener.launcher(bottle)),
              dest=str(launcher), mode="755", create_remote_dir=True)
    icon = home / ".local/share/icons/hicolor/256x256/apps/scrivener.png"
    server.shell(name="Scrivener icon (from Scrivener.exe)", _shell_executable="bash",
                 commands=[wine.icon_script(directory / "Scrivener.exe", icon)])
    files.put(name="Scrivener application menu entry", src=StringIO(wine.desktop_entry(
        "Scrivener", "Writing studio for long manuscripts", launcher, icon, "Office;WordProcessor;", "scrivener.exe")),
        dest=str(home / ".local/share/applications/scrivener.desktop"), mode="644", create_remote_dir=True)
