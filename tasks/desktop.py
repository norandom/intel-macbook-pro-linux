"""Hyprland desktop (P14-P18 of norandom/hyperland-forky-worker-vm @ a1c09ec), native backport.

Ubuntu's packaged Hyprland 0.53.3 + hyprbars 0.53 (ABI hyprland-abi-6d24081), native GPU.
The source's Lua config (Hyprland 0.56) is translated into 0.53 conf fragments; its
callbacks/timers run in one session worker (hypr-windows). The session entry
"Hyprland (uwsm-managed)" comes from the hyprland package; SDDM, autologin, KDE and the
audio stack are untouched. Session services are wanted by hypr-desktop.target only,
which the Hyprland config starts, so nothing runs in a KDE login.

Run:  .venv/bin/pyinfra @local tasks/desktop.py [--dry]
"""
import os
import socket
from io import StringIO
from pathlib import Path

from pyinfra import host, local, logger
from pyinfra.facts.files import File, FindInFile
from pyinfra.operations import files, server
from pyinfra.operations.util import any_changed

from manage.desktop_hostcolor import color_for
from manage.packages import PackageRequest, install_packages
from manage.preflight import validate_local_context
from manage.userconfig import setting

validate_local_context()
local.include("tasks/package_policy.py")

SRC = "files/desktop"
TPL = "templates/desktop"
MARKER = "Managed by t2-mac-kde (desktop)"
home = os.path.expanduser("~")
cfg = f"{home}/.config"
hypr = f"{cfg}/hypr"
bin_dir = f"{home}/.local/bin"

# Source defaults (group_data/all.py); override in host data.
decorations_style = setting("decorations_style", "win311")
window_shadows = setting("window_shadows", "off")
bar_graphs = bool(setting("bar_graphs", False))
# Optional strip at the internal panel's left edge kept free (config desktop_left_reserve; 0 = off).
left_reserve = int(setting("desktop_left_reserve", 0))
panel_scale = str(setting("panel_scale", "auto"))
font_rendering = setting("font_rendering", "rgb")

# --- Native packages (no recommends: Snap/Flatpak-free, guarded by manage.packages) --------
# Audio (PipeWire/WirePlumber/pipewire-pulse), fonts, terminals and applications belong to
# their own features and are not requested here. Excluded: hyprland-guiutils (unused),
# software-rendering mesa packages (VM only), fuse3/pulseaudio-utils (RDP only).
# Xfe is installed by tasks/xfe.py (unpacked Ubuntu archive; its apt Conflicts: im-config
# would remove a KDE-base package). SUPER+E and the bar button launch it.
install_packages(PackageRequest(
    packages=(
        "hyprland", "hyprland-plugin-hyprbars", "uwsm",
        "xdg-desktop-portal-hyprland", "xdg-desktop-portal-gtk", "xwayland",
        "waybar", "mako-notifier", "fuzzel", "hyprlock",
        "python3-gi", "gir1.2-gtk-3.0", "gir1.2-gtklayershell-0.1",
        "wl-clipboard", "cliphist", "jq", "adwaita-icon-theme",
        # laptop layer (files/desktop/hypr/laptop.conf)
        "hyprland-qtutils", "hypridle", "hyprpolkitagent", "grim", "slurp", "playerctl",
        "network-manager-gnome", "blueman", "libnotify-bin",
        "libgtk-4-1", "libadwaita-1-0",  # Satty (screenshot annotation, below)
    ),
    source="ubuntu",
))


def owned_put(src, dest, mode="644", template=False, **data):
    """Write a desktop-owned file unless an unmanaged user file is already there."""
    if host.get_fact(File, path=dest) and not host.get_fact(FindInFile, path=dest, pattern=MARKER):
        logger.warning(f"desktop: {dest} exists and is not ours; left unchanged")
        return None
    op = files.template if template else files.put
    return op(name=f"Desktop: {dest}", src=src, dest=dest, mode=mode, create_remote_dir=True, **data)


def seed(src, dest, mode="644"):
    """Initial copy only: an existing (e.g. KDE-managed or user-edited) file is kept."""
    if host.get_fact(File, path=dest):
        logger.info(f"desktop: {dest} already exists; initial seed skipped")
        return None
    return files.put(name=f"Seed (once): {dest}", src=src, dest=dest, mode=mode, create_remote_dir=True)


def once(path, value):
    server.shell(name=f"Switch file {path} (set once to {value})",
                 commands=[f"mkdir -p '{os.path.dirname(path)}'; [ -s '{path}' ] || echo {value} > '{path}'"])


# --- Hyprland configuration -------------------------------------------------------------------
once(f"{hypr}/decorations-style", decorations_style)
once(f"{hypr}/window-shadows", window_shadows)
once(f"{hypr}/layout-mode", "dynamic")

# Hyprland reloads on every change of hyprland.conf: write everything it sources first
# (generated files, other confs, bindings, shaders) and hyprland.conf itself last, so a
# deploy never triggers "source= globbing error: found no match".
hypr_ops = []
# Internal panel scale from the user config (panel_scale; "auto" = Hyprland's choice).
hypr_ops.append(owned_put(
    StringIO(f"# {MARKER}: panel_scale = {panel_scale} (~/.config/t2-mac-kde/config.toml)\n"
             + ("" if panel_scale == "auto" else f"monitor = eDP-1, preferred, auto, {panel_scale}\n")),
    f"{hypr}/panel.conf"))

# Host colour (source tools/hostcolor.py) from this machine's hostname: bars and borders.
hostname = socket.gethostname()
hc = color_for(hostname, setting("decor_colors", {}).get(hostname), setting("fleet_hosts", []))
hypr_ops.append(owned_put(
    StringIO(f"# {MARKER} (tools/hostcolor): colour of {hostname}, white text {hc['contrast']}:1\n"
             f"$host_color = {hc['hex']}\n$host_pale = {hc['pale']}\n"),
    f"{hypr}/hostcolor.conf"))

conf_names = sorted(p.name for p in Path(SRC, "hypr").glob("*.conf") if p.name != "hyprland.conf")
hypr_ops += [owned_put(f"{SRC}/hypr/{n}", f"{hypr}/{n}") for n in conf_names]
hypr_ops.append(owned_put(f"{TPL}/bindings.conf.j2", f"{hypr}/bindings.conf", template=True))
for shader in ("night-green.glsl", "night-dark.glsl"):
    hypr_ops.append(owned_put(f"{SRC}/hypr/shaders/{shader}", f"{hypr}/shaders/{shader}"))
hypr_ops.append(owned_put(f"{SRC}/hypr/hyprland.conf", f"{hypr}/hyprland.conf"))

# --- Helpers (~/.local/bin) --------------------------------------------------------------------
HELPERS = (
    "hypr-desktop-state", "hypr-launch", "hypr-deco", "hypr-shadow", "hypr-layout", "hypr-pin",
    "hypr-glass", "hypr-kbd", "hypr-nightmode", "hypr-windows", "hypr-session", "hypr-appmenu",
    "hypr-sparkline", "hypr-agent-quota", "hypr-cliphist", "hypr-clip-bridge", "hypr-termtheme-status",
    "hypr-brightness", "hypr-screenshot", "hypr-osd", "hypr-volume", "hypr-power-profile",
)
helper_ops = [owned_put(f"{SRC}/bin/{h}", f"{bin_dir}/{h}", mode="755") for h in HELPERS]

# Satty: Greenshot-style screenshot annotation (arrows, boxes, text, blur, crop). Not in
# Ubuntu; upstream release binary, pinned + sha256, user-level. hypr-screenshot opens it.
SATTY_VERSION = "0.22.0"
SATTY_SHA256 = "eb7a028c4a5ce331c2f355add8e2b807a7d697fe4495f7e1965786a4f6bcd5b8"
satty_dir = f"{home}/.local/opt/satty-{SATTY_VERSION}"
server.shell(
    name=f"Satty {SATTY_VERSION} (screenshot editor, checksum verified)",
    commands=[f"""set -e
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
curl -fsSL -o "$t/satty.tgz" https://github.com/Satty-org/Satty/releases/download/v{SATTY_VERSION}/satty-x86_64-unknown-linux-gnu.tar.gz
echo "{SATTY_SHA256}  $t/satty.tgz" | sha256sum -c --quiet -
mkdir -p "$t/x" && tar xzf "$t/satty.tgz" -C "$t/x"
"$t/x/satty" --version >/dev/null
mkdir -p {satty_dir} {bin_dir} {home}/.local/share/bash-completion/completions
install -m 755 "$t/x/satty" {satty_dir}/satty
ln -sfn {satty_dir}/satty {bin_dir}/satty
install -m 644 "$t/x/completions/satty.bash" {home}/.local/share/bash-completion/completions/satty"""],
    _if=lambda: not os.path.exists(f"{satty_dir}/satty"),
)

# state.conf: layout / title bar style / shadows + the package-owned hyprbars path (dpkg).
server.shell(name="Hyprland: render state.conf (layout, title bars, shadows, hyprbars path)",
             commands=[f"{bin_dir}/hypr-desktop-state"])

# Reload a running Hyprland only when it is the single instance of this user (never "newest").
server.shell(
    name="Reload running Hyprland (config changed)",
    commands=['d="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/hypr"; set -- "$d"/*/.socket.sock; '
              '[ $# -eq 1 ] && [ -S "$1" ] || exit 0; sig=$(basename "$(dirname "$1")"); '
              'HYPRLAND_INSTANCE_SIGNATURE=$sig hyprctl reload >/dev/null || true'],
    _if=any_changed(*[o for o in hypr_ops + helper_ops if o]),
)

# --- Bar, notifications, launcher, lock, file manager, GTK ---------------------------------
bar_ops = [
    owned_put(f"{TPL}/waybar-config.jsonc.j2", f"{cfg}/waybar/config.jsonc", template=True, bar_graphs=bar_graphs, left_reserve=left_reserve),
    owned_put(f"{SRC}/waybar/style.css", f"{cfg}/waybar/style.css"),
    files.put(name="Waybar: power button artwork", src=f"{SRC}/waybar/power.png",
              dest=f"{cfg}/waybar/power.png", mode="644", create_remote_dir=True),
]
owned_put(f"{SRC}/mako/config", f"{cfg}/mako/config")
owned_put(f"{SRC}/fuzzel/fuzzel.ini", f"{cfg}/fuzzel/fuzzel.ini")
seed(f"{SRC}/xdg-terminals.list", f"{cfg}/xdg-terminals.list")
seed(f"{SRC}/xfe/xferc", f"{cfg}/xfe/xferc")   # Windows 3.11 colours; Xfe keeps user changes
# GTK settings.ini is shared with KDE (kde-gtk-config): only seeded when absent.
if not host.get_fact(File, path=f"{cfg}/gtk-3.0/settings.ini"):
    files.template(name="Seed (once): GTK 3 settings", src=f"{TPL}/gtk-settings.ini.j2",
                   dest=f"{cfg}/gtk-3.0/settings.ini", mode="644", create_remote_dir=True,
                   font_rendering=font_rendering)
else:
    logger.info("desktop: ~/.config/gtk-3.0/settings.ini exists (KDE); initial seed skipped")

# uwsm session environment for Hyprland (source file; no llvmpipe / software rendering).
owned_put(StringIO(f"# {MARKER}\nexport XCURSOR_THEME=Adwaita\nexport XCURSOR_SIZE=24\n"),
          f"{cfg}/uwsm/env-hyprland")

# --- Session-scoped user services -----------------------------------------------------------------
UNITS = ("hypr-desktop.target", "hypr-windows.service", "hypr-clip-bridge.service",
         "hypr-cliphist.service", "hypr-cliphist-wipe.service", "hypr-cliphist-wipe.timer",
         "hypr-tailscale-tray.service")
unit_ops = [owned_put(f"{SRC}/systemd/{u}", f"{cfg}/systemd/user/{u}") for u in UNITS]
server.shell(name="systemd --user daemon-reload (desktop units changed)", commands=["systemctl --user daemon-reload"],
             _if=any_changed(*[o for o in unit_ops if o]))
# enable = link into hypr-desktop.target.wants only (no --now: nothing starts in this KDE login).
server.shell(
    name="Desktop services wanted by hypr-desktop.target (waybar, worker, clipboard, 01:00 wipe)",
    commands=["systemctl --user enable hypr-windows.service hypr-clip-bridge.service "
              "hypr-cliphist.service hypr-cliphist-wipe.timer hypr-tailscale-tray.service",
              "systemctl --user add-wants hypr-desktop.target waybar.service"],
)
server.shell(
    name="Reload waybar of a running Hyprland session (bar changed)",
    commands=["systemctl --user is-active -q hypr-desktop.target && "
              "systemctl --user reload-or-restart waybar.service || true"],
    _if=any_changed(*[o for o in bar_ops if o]),
)

# --- Session entry check: from the hyprland package, SDDM unchanged ---------------------------
server.shell(
    name="Check: 'Hyprland (uwsm-managed)' session entry is package-owned",
    commands=["dpkg-query -S /usr/share/wayland-sessions/hyprland-uwsm.desktop"],
)
