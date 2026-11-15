"""Coordinated terminal/app themes (P19-P20 of norandom/hyperland-forky-worker-vm @ a1c09ec).

Five palettes, one per Terminator profile: default (cobalt), navy, fixedsys, cream, petrol.
hypr-termtheme switches them together; hypr-term launches Terminator with the current one.
App assets go only where the app is present; nothing is installed (application-suite owns
Terminator/foot/Ghostty/...). Run:  .venv/bin/pyinfra @local tasks/themes.py [--dry]
"""
import os
import shutil

from pyinfra import host, logger
from pyinfra.facts.files import File, FindInFile
from pyinfra.operations import files, server

from manage.preflight import validate_local_context
from manage.userconfig import setting

validate_local_context()

SRC = "files/themes"
THEMES = ("cobalt", "navy", "fixedsys", "cream", "petrol")
MARKER = "Managed by debian-hypr"
home = os.path.expanduser("~")
cfg = f"{home}/.config"


def present(command, *paths):
    """App is installed (on PATH) or already has its user directory."""
    return bool(shutil.which(command)) or any(os.path.isdir(p) for p in paths)


def managed_put(src, dest, mode="644"):
    """Install a source config unless an unmanaged user file is already there."""
    if host.get_fact(File, path=dest) and not host.get_fact(FindInFile, path=dest, pattern=MARKER):
        logger.warning(f"themes: {dest} exists and is not ours; left unchanged (theme include not added)")
        return
    files.put(name=f"Config: {dest}", src=src, dest=dest, mode=mode)


# --- Terminator: five profiles, Theme menu plugin, slim tab line ---------------------------
term_cfg = f"{cfg}/terminator/config"
if host.get_fact(File, path=term_cfg) and not host.get_fact(FindInFile, path=term_cfg, pattern=r"^  \[\[petrol\]\]"):
    server.shell(name="Terminator: back up existing config before installing the theme profiles",
                 commands=[f'[ -e "{term_cfg}.pre-t2-mac-kde" ] || cp -p "{term_cfg}" "{term_cfg}.pre-t2-mac-kde"'])
    files.put(name="Terminator: config with the five theme profiles", src=f"{SRC}/terminator/config",
              dest=term_cfg, mode="644")
elif not host.get_fact(File, path=term_cfg):
    files.put(name="Terminator: config with the five theme profiles", src=f"{SRC}/terminator/config",
              dest=term_cfg, mode="644")
files.put(name="Terminator: Theme menu plugin", src=f"{SRC}/terminator/plugins/theme_menu.py",
          dest=f"{cfg}/terminator/plugins/theme_menu.py", mode="644")

# Tab styling as its own file, imported first in gtk.css (KDE keeps its own imports there).
files.put(name="GTK: Terminator tab line CSS", src=f"{SRC}/gtk-3.0/terminator-tabs.css",
          dest=f"{cfg}/gtk-3.0/t2-mac-kde-terminator-tabs.css", mode="644")
gtk_css = f"{cfg}/gtk-3.0/gtk.css"
imp = "@import url(\"t2-mac-kde-terminator-tabs.css\");"
if not host.get_fact(FindInFile, path=gtk_css, pattern="t2-mac-kde-terminator-tabs.css"):
    server.shell(
        name="GTK: import the Terminator tab line in gtk.css (prepended, rest kept)",
        commands=[f"f='{gtk_css}'; touch \"$f\"; grep -qF 't2-mac-kde-terminator-tabs.css' \"$f\" || "
                  f"{{ t=$(mktemp \"$f.XXXXXX\") && printf '%s\\n' '{imp}' | cat - \"$f\" > \"$t\" && "
                  f"chmod 644 \"$t\" && mv \"$t\" \"$(readlink -f \"$f\")\"; }}"],
    )

# --- Commands ---------------------------------------------------------------------------
files.put(name="hypr-termtheme (theme switch)", src=f"{SRC}/bin/hypr-termtheme",
          dest=f"{home}/.local/bin/hypr-termtheme", mode="755")
files.put(name="hypr-term (Terminator with the chosen theme)", src=f"{SRC}/bin/hypr-term",
          dest="/usr/local/bin/hypr-term", mode="755", _sudo=True)

# --- Per-app theme assets (only for apps that are present) ----------------------------------
if present("btop", f"{cfg}/btop"):
    for t in THEMES:
        files.put(name=f"btop theme ({t})", src=f"{SRC}/btop/{t}.theme",
                  dest=f"{cfg}/btop/themes/{t}.theme", mode="644")

if present("claude", f"{home}/.claude"):
    for t in THEMES:
        files.put(name=f"Claude Code theme ({t})", src=f"{SRC}/claude/{t}.json",
                  dest=f"{home}/.claude/themes/{t}.json", mode="600")

if present("ghostty", f"{cfg}/ghostty"):
    for t in THEMES:
        for ext in ("", ".css"):
            files.put(name=f"Ghostty theme ({t}{ext})", src=f"{SRC}/ghostty/themes/{t}{ext}",
                      dest=f"{cfg}/ghostty/themes/{t}{ext}", mode="644")
    managed_put(f"{SRC}/ghostty/config.ghostty", f"{cfg}/ghostty/config.ghostty")

if present("foot", f"{cfg}/foot"):
    for t in THEMES:
        files.put(name=f"foot theme ({t})", src=f"{SRC}/foot/themes/{t}.ini",
                  dest=f"{cfg}/foot/themes/{t}.ini", mode="644")
    managed_put(f"{SRC}/foot/foot.ini", f"{cfg}/foot/foot.ini")

if present("subl", f"{cfg}/sublime-text"):
    for t in THEMES:
        name = f"debian-hypr-{t}.sublime-color-scheme"
        files.put(name=f"Sublime Text colour scheme ({t})", src=f"{SRC}/sublime/{name}",
                  dest=f"{cfg}/sublime-text/Packages/User/{name}", mode="644")

for data, conf, cmd in ((".vscode", "Code", "code"), (".positron", "Positron", "positron")):
    if present(cmd, f"{cfg}/{conf}"):
        files.sync(name=f"{conf}: debian-hypr themes extension", src=f"{SRC}/vscode/debian-hypr-themes/",
                   dest=f"{home}/{data}/extensions/debian-hypr.debian-hypr-themes-1.0.0")

if present("nvim"):
    files.put(name="Neovim: Berg light for cream, dark otherwise (next start)",
              src=f"{SRC}/nvim/plugin/debian-hypr-theme.lua",
              dest=f"{cfg}/nvim/plugin/debian-hypr-theme.lua", mode="644")

# --- xfce4-terminal: source cobalt settings + unsafe-paste review (not cycled) ---------------
if shutil.which("xfce4-terminal") and shutil.which("xfconf-query"):
    palette = ";".join((
        "#00347d", "#e87a74", "#7ac48a", "#f1dc9a", "#8bb4e0", "#b89cd9", "#6f88a7", "#e8dfc9",
        "#1453af", "#e87a74", "#7ac48a", "#ffe9a8", "#8bb4e0", "#d29acb", "#8bb4e0", "#fff8f0",
    ))
    props = {
        "/misc-show-unsafe-paste-dialog": ("bool", "true"), "/misc-cursor-blinks": ("bool", "false"),
        "/color-use-theme": ("bool", "false"), "/color-background": ("string", "#0049b2"),
        "/color-foreground": ("string", "#fff8f0"), "/color-cursor": ("string", "#f1dc9a"),
        "/color-cursor-use-default": ("bool", "false"), "/color-palette": ("string", palette),
        "/font-use-system": ("bool", "false"), "/font-name": ("string", "FiraCode Nerd Font 11"),
        "/misc-menubar-default": ("bool", "false"), "/scrolling-bar": ("string", "TERMINAL_SCROLLBAR_NONE"),
    }
    # Only on the running session bus; without one this is skipped (re-run from the desktop).
    server.shell(
        name="xfce4-terminal: cobalt theme, paste review dialog (needs the session bus)",
        commands=['[ -S "${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/bus" ] || { echo "no session bus: skipped"; exit 0; }']
        + [f"xfconf-query -c xfce4-terminal -p {p} -s '{v}' 2>/dev/null || "
           f"xfconf-query -c xfce4-terminal -p {p} -n -t {t} -s '{v}'" for p, (t, v) in props.items()],
    )

# --- Chromium frame colour: constant cream, explicit opt-in (native /etc/chromium only) -------
if setting("themes_chromium_policy") and os.path.isdir("/etc/chromium"):
    files.put(name="Chromium theme colour policy (cream)", src=f"{SRC}/chromium/debian-hypr-theme.json",
              dest="/etc/chromium/policies/managed/debian-hypr-theme.json", mode="644", _sudo=True)

# --- Apply the current profile to everything above -----------------------------------------
server.shell(name="Apps follow the current terminal profile (hypr-termtheme apply)",
             commands=[f"{home}/.local/bin/hypr-termtheme apply"])
