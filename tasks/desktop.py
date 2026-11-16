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
from manage.pixel_snap import conf as pixel_snap_conf
from manage import password_store
from manage.packages import PackageRequest, install_packages
from manage.preflight import validate_local_context
from manage.userconfig import setting
from manage.nix_tools import SESSION_PATH as nix_session_path

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
# Pointer: "t2-highvis" = large white arrow with a red outline (tools/make_cursor.py).
cursor_theme = str(setting("cursor_theme", "breeze_cursors"))
cursor_size = int(setting("cursor_size", 24))
font_rendering = setting("font_rendering", "grayscale")  # same default as tasks/fonts.py

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
        "python3-secretstorage",  # hypr-wallet-check
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

# Whole-pixel border / title bar at a fractional panel scale (sourced last in hyprland.conf).
hypr_ops.append(owned_put(
    StringIO(f"# {MARKER}: panel_scale = {panel_scale}\n"
             + pixel_snap_conf(panel_scale, 2, 22 if decorations_style == "win311" else 24)),
    f"{hypr}/pixel-snap.conf"))

# Pointer theme + size for Hyprland, Xwayland and GTK/portal apps (config cursor_theme/size).
hypr_ops.append(owned_put(
    StringIO(f"# {MARKER}: cursor_theme = {cursor_theme}, cursor_size = {cursor_size}\n"
             f"env = XCURSOR_THEME,{cursor_theme}\nenv = XCURSOR_SIZE,{cursor_size}\n"
             f"env = HYPRCURSOR_SIZE,{cursor_size}\n"
             f"exec-once = hyprctl setcursor {cursor_theme} {cursor_size}\n"),
    f"{hypr}/cursor.conf"))

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
    "hypr-brightness", "hypr-screenshot", "hypr-osd", "hypr-volume", "hypr-power-profile", "hypr-findcursor", "hypr-netrate", "hypr-thermal", "hypr-touchpad", "hypr-gpu", "hypr-wallet-check",
)
helper_ops = [owned_put(f"{SRC}/bin/{h}", f"{bin_dir}/{h}", mode="755") for h in HELPERS]

# Hibernate (config hibernate, default off): needs disk swap >= RAM (docs/hibernate-swap.md).
# Ubuntu's polkit rules forbid it for everyone; ours allows the active local session.
hibernate = setting("hibernate", False)
if not isinstance(hibernate, bool):
    raise ValueError("hibernate must be true or false")
if hibernate:
    owned_put(f"{SRC}/bin/hypr-hibernate", f"{bin_dir}/hypr-hibernate", mode="755")
    rule = files.put(name="polkit: allow hibernate for the active local session", src=f"{SRC}/polkit/49-t2-hibernate.rules",
                     dest="/etc/polkit-1/rules.d/49-t2-hibernate.rules", mode="644", _sudo=True)
    files.put(name="systemd-sleep: HibernateMode=shutdown (no ACPI S4 firmware call)",
              src=f"{SRC}/systemd-sleep/t2-hibernate.conf", dest="/etc/systemd/sleep.conf.d/t2-hibernate.conf",
              mode="644", create_remote_dir=True, _sudo=True)
    # Owner-approved boundary exception (2026-11-16): unload the T2 bridge drivers before
    # hibernate, load them fresh after the restore (the T2 chip is power-cycled). Hibernate only.
    bce = [files.put(name="T2 driver hook for hibernate (/usr/local/libexec/t2-hibernate-bce)",
                     src=f"{SRC}/t2-hibernate-bce", dest="/usr/local/libexec/t2-hibernate-bce", mode="755",
                     create_remote_dir=True, _sudo=True),
           files.put(name="t2-hibernate-bce.service (required by systemd-hibernate.service)",
                     src=f"{SRC}/systemd-system/t2-hibernate-bce.service",
                     dest="/etc/systemd/system/t2-hibernate-bce.service", mode="644", _sudo=True)]
    server.shell(name="Enable t2-hibernate-bce.service", _sudo=True,
                 _if=lambda: any(op.did_change() for op in bce),
                 commands=["systemctl daemon-reload", "systemctl reenable t2-hibernate-bce.service"])
else:
    server.shell(name="t2-hibernate-bce.service off (hibernate off)", _sudo=True, commands=[
        "[ ! -e /etc/systemd/system/t2-hibernate-bce.service ] || { systemctl disable t2-hibernate-bce.service; "
        "rm -f /etc/systemd/system/t2-hibernate-bce.service /usr/local/libexec/t2-hibernate-bce; "
        "systemctl daemon-reload; }"])
    files.file(name="systemd-sleep hibernate mode removed (hibernate off)",
               path="/etc/systemd/sleep.conf.d/t2-hibernate.conf", present=False, _sudo=True)
    files.file(name="hypr-hibernate removed (hibernate off)", path=f"{bin_dir}/hypr-hibernate", present=False)
    rule = files.file(name="polkit hibernate rule removed (hibernate off)",
                      path="/etc/polkit-1/rules.d/49-t2-hibernate.rules", present=False, _sudo=True)
# Lid close (config lid_close: "suspend" default | "hibernate"; hibernate needs hibernate = true).
# HandleLidSwitch also covers external power; docked (external monitor) stays logind's "ignore".
lid_close = setting("lid_close", "suspend")
if lid_close not in ("suspend", "hibernate"):
    raise ValueError('lid_close must be "suspend" or "hibernate"')
if lid_close == "hibernate" and not hibernate:
    logger.warning('lid_close = "hibernate" needs hibernate = true; closing the lid keeps suspending')
    lid_close = "suspend"
lid = (files.put(name="logind: lid close hibernates", dest="/etc/systemd/logind.conf.d/t2-lid.conf", mode="644",
                 create_remote_dir=True, _sudo=True,
                 src=StringIO("# Managed by t2-mac-kde (desktop, config lid_close)\n[Login]\n"
                              "HandleLidSwitch=hibernate\nHandleLidSwitchExternalPower=hibernate\n"))
       if lid_close == "hibernate" else
       files.file(name="logind: lid close back to suspend (default)", path="/etc/systemd/logind.conf.d/t2-lid.conf",
                  present=False, _sudo=True))
# logind re-reads its config on SIGHUP; a restart would end the session.
server.shell(name="logind: reload lid setting (SIGHUP, no restart)", _if=lid.did_change, _sudo=True,
             commands=["systemctl kill -s HUP --kill-whom=main systemd-logind.service"])
# polkitd reloads rules on inotify, but it saw the file before its chmod 644 ("Error loading
# script") and doesn't retry: restart it after a change (agents reconnect by themselves).
server.shell(name="Restart polkit to load the hibernate rule", _if=rule.did_change, _sudo=True,
             commands=["systemctl restart polkit.service"])

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

# High-visibility cursor theme (user-level icon theme; selected via cursor_theme).
icons = f"{home}/.local/share/icons/t2-highvis"
files.put(name="Cursor theme t2-highvis: index", src=f"{SRC}/cursors/t2-highvis/index.theme",
          dest=f"{icons}/index.theme", mode="644", create_remote_dir=True)
files.put(name="Cursor theme t2-highvis: arrow", src=f"{SRC}/cursors/t2-highvis/cursors/left_ptr",
          dest=f"{icons}/cursors/left_ptr", mode="644", create_remote_dir=True)
for alias in ("default", "arrow", "top_left_arrow", "left_arrow", "pointer-default"):
    files.link(name=f"Cursor theme t2-highvis: {alias}", path=f"{icons}/cursors/{alias}", target="left_ptr")
server.shell(name=f"GTK/portal apps: cursor {cursor_theme} {cursor_size}", commands=[
    f"[ \"$(gsettings get org.gnome.desktop.interface cursor-theme)\" = \"'{cursor_theme}'\" ] || "
    f"gsettings set org.gnome.desktop.interface cursor-theme '{cursor_theme}'",
    f"[ \"$(gsettings get org.gnome.desktop.interface cursor-size)\" = '{cursor_size}' ] || "
    f"gsettings set org.gnome.desktop.interface cursor-size {cursor_size}"])

# Chromium/Electron password backend in Hyprland = the one KDE uses (wallet), so saved
# passwords stay readable in both sessions (config: password_store; "" disables).
store = str(setting("password_store", "kwallet6" if os.path.exists("/usr/bin/kwalletd6") else "gnome-libsecret"))
for app in (password_store.APPS if store else ()):
    system_entry = Path("/usr/share/applications", app)
    if system_entry.is_file():
        files.put(name=f"{app}: --password-store={store}", dest=f"{home}/.local/share/applications/{app}",
                  src=StringIO(password_store.override(system_entry.read_text(), store)),
                  mode="644", create_remote_dir=True)

# Default applications per MIME type from the user config, e.g. PDFs -> PdfCraft:
#   [default_apps]  "application/pdf" = "ai.storyteller.pdfcraft.desktop"
for mime, app in dict(setting("default_apps", {})).items():
    server.shell(name=f"Default app for {mime}: {app}",
                 commands=[f"[ \"$(xdg-mime query default {mime})\" = '{app}' ] || xdg-mime default '{app}' {mime}"])

# hyprbars with our input fix (files/desktop/hyprbars): Ubuntu's 0.53.0 lets the focused
# window's bar take clicks meant for the window above it (no raise) and can miss a release
# (lost double-click = no unmaximize, window left on the pointer). Built as the user from the
# pinned upstream tarball against hyprland-dev; rebuilt when Hyprland or the patch changes.
install_packages(PackageRequest(
    packages=("hyprland-dev", "libgles-dev", "libpango1.0-dev", "libudev-dev", "libpixman-1-dev", "pkgconf", "g++", "make", "patch"),
    source="ubuntu",
))
bars_dir = f"{home}/.local/share/t2-mac-kde/hyprbars"
files.put(name="hyprbars: input patch", src=f"{SRC}/hyprbars/hyprbars-0.53.0-t2-input.patch",
          dest=f"{bars_dir}/hyprbars-0.53.0-t2-input.patch", mode="644", create_remote_dir=True)
files.put(name="hyprbars: build script", src=f"{SRC}/hyprbars/build-hyprbars",
          dest=f"{bars_dir}/build-hyprbars", mode="755", create_remote_dir=True)
server.shell(name="hyprbars 0.53.0 + input patch -> ~/.local/lib/t2-mac-kde/hyprbars (sha256 verified)",
             commands=[f"{bars_dir}/build-hyprbars {bars_dir}/hyprbars-0.53.0-t2-input.patch"])

# state.conf: layout / title bar style / shadows + the hyprbars path (patched build or dpkg).
# --reload: a running Hyprland picks up a changed state.conf (e.g. the patched plugin).
server.shell(name="Hyprland: render state.conf (layout, title bars, shadows, hyprbars path)",
             commands=[f"{bin_dir}/hypr-desktop-state --reload"])

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
    owned_put(f"{TPL}/waybar-config.jsonc.j2", f"{cfg}/waybar/config.jsonc", template=True, bar_graphs=bar_graphs, left_reserve=left_reserve, hibernate=hibernate),
    owned_put(f"{SRC}/waybar/style.css", f"{cfg}/waybar/style.css"),
    owned_put(f"{SRC}/waybar/power-profile-menu.xml", f"{cfg}/waybar/power-profile-menu.xml"),
    files.put(name="Waybar: power button artwork", src=f"{SRC}/waybar/power.png",
              dest=f"{cfg}/waybar/power.png", mode="644", create_remote_dir=True),
]
owned_put(f"{SRC}/mako/config", f"{cfg}/mako/config")
owned_put(f"{SRC}/fuzzel/fuzzel.ini", f"{cfg}/fuzzel/fuzzel.ini")
seed(f"{SRC}/xdg-terminals.list", f"{cfg}/xdg-terminals.list")
seed(f"{SRC}/xfe/xferc", f"{cfg}/xfe/xferc")   # Windows 3.11 colours; Xfe keeps user changes
seed(f"{SRC}/hypr/touchpad.conf", f"{cfg}/hypr/touchpad.conf")   # hypr-touchpad owns it afterwards
# GTK settings.ini is shared with KDE (kde-gtk-config): only seeded when absent.
if not host.get_fact(File, path=f"{cfg}/gtk-3.0/settings.ini"):
    files.template(name="Seed (once): GTK 3 settings", src=f"{TPL}/gtk-settings.ini.j2",
                   dest=f"{cfg}/gtk-3.0/settings.ini", mode="644", create_remote_dir=True,
                   font_rendering=font_rendering)
else:
    logger.info("desktop: ~/.config/gtk-3.0/settings.ini exists (KDE); initial seed skipped")

# uwsm session environment for Hyprland, sourced before Hyprland starts: cursor from the config,
# and the GPU set from hypr-gpu's mode file (battery = Intel only; external = Intel + AMD outputs).
# AQ_DRM_DEVICES is only set when the udev names exist, so a missing rule never blanks the session.
# Nix profile first in PATH, so launchers see the Nix tools (tasks/nix_tools.py).
gpu_mode = str(setting("gpu_mode", "battery"))
gpu_state = f"{home}/.local/state/t2-mac-kde/gpu-mode"
if not os.path.exists(gpu_state):
    files.put(name=f"GPU mode seed: {gpu_mode} (config gpu_mode; hypr-gpu changes it)", src=StringIO(gpu_mode + "\n"),
              dest=gpu_state, mode="644", create_remote_dir=True)
owned_put(StringIO(
    f"# {MARKER}\n"
    f"export XCURSOR_THEME={cursor_theme}\nexport XCURSOR_SIZE={cursor_size}\n"
    'if [ -e /dev/dri/intel-igpu ]; then\n'
    f'  case "$(cat "{gpu_state}" 2>/dev/null)" in\n'
    '    external) if [ -e /dev/dri/amd-dgpu ]; then export AQ_DRM_DEVICES=/dev/dri/intel-igpu:/dev/dri/amd-dgpu; fi ;;\n'
    '    *) export AQ_DRM_DEVICES=/dev/dri/intel-igpu ;;\n'
    '  esac\n'
    'fi\n'
    + nix_session_path), f"{cfg}/uwsm/env-hyprland")
gpu_rule = files.put(name="udev: stable GPU names /dev/dri/intel-igpu, /dev/dri/amd-dgpu", src=f"{SRC}/udev/61-t2-gpu-names.rules",
                     dest="/etc/udev/rules.d/61-t2-gpu-names.rules", mode="644", _sudo=True)
server.shell(name="udev: apply the GPU names now", _if=gpu_rule.did_change, _sudo=True,
             commands=["udevadm control --reload", "udevadm trigger --subsystem-match=drm --action=change"])

# --- Session-scoped user services -----------------------------------------------------------------
UNITS = ("hypr-desktop.target", "hypr-windows.service", "hypr-clip-bridge.service",
         "hypr-cliphist.service", "hypr-cliphist-wipe.service", "hypr-cliphist-wipe.timer",
         "hypr-tailscale-tray.service", "hypr-secret-service.service")
unit_ops = [owned_put(f"{SRC}/systemd/{u}", f"{cfg}/systemd/user/{u}") for u in UNITS]
server.shell(name="systemd --user daemon-reload (desktop units changed)", commands=["systemctl --user daemon-reload"],
             _if=any_changed(*[o for o in unit_ops if o]))
# enable = link into hypr-desktop.target.wants only (no --now: nothing starts in this KDE login).
server.shell(
    name="Desktop services wanted by hypr-desktop.target (waybar, worker, clipboard, 01:00 wipe)",
    commands=["systemctl --user enable hypr-windows.service hypr-clip-bridge.service "
              "hypr-cliphist.service hypr-cliphist-wipe.timer hypr-tailscale-tray.service hypr-secret-service.service",
              "systemctl --user add-wants hypr-desktop.target waybar.service"],
)
worker_op = helper_ops[HELPERS.index("hypr-windows")]
if worker_op:
    server.shell(
        name="Restart the window worker of a running Hyprland session (hypr-windows changed)",
        commands=["systemctl --user is-active -q hypr-windows.service && "
                  "systemctl --user restart hypr-windows.service || true"],
        _if=worker_op.did_change,
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
