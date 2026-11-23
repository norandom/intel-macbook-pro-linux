"""Keep Hyprland services out of KDE, and give KDE the same black left strip.

The Ubuntu packages of waybar, mako, hypridle and hyprpolkitagent enable themselves for every
graphical session (/etc/systemd/user/graphical-session.target.wants, package-owned). A KDE
login reaches that target too, so the Hyprland bar, notifications, idle rules (hyprctl dpms,
dim, lock) and polkit agent came up inside Plasma. A per-user drop-in limits them to
Hyprland sessions; the package links stay untouched.

The black strip over the panel's defective left edge (desktop_left_reserve) is a Waybar
layer-shell bar in Hyprland. In KDE, t2-leftstrip draws it (files/desktop/bin/t2-leftstrip):
Plasma keeps windows, icons, panels and the start menu clear only of its own panels, so the
helper keeps an empty Plasma panel of that width and paints black over it. The width is
converted to KDE's scale so it covers the same physical pixels.
"""
import json
from pathlib import Path

HYPRLAND_ONLY = ("waybar.service", "mako.service", "hypridle.service", "hyprpolkitagent.service")
DROPIN = "t2-hyprland-only.conf"
KDE_STRIP_UNIT = "t2-kde-leftstrip.service"
OLD_KDE_STRIP_CONFIG = "leftstrip-kde.jsonc"   # Waybar strip before t2-leftstrip; removed


def hyprland_only_dropin(marker: str) -> str:
    return (f"# {marker}: the package enables this unit for every graphical session; KDE sets\n"
            "# XDG_CURRENT_DESKTOP=KDE, uwsm exports Hyprland before the session target starts.\n"
            "[Unit]\nConditionEnvironment=XDG_CURRENT_DESKTOP=Hyprland\n")


def kde_scale(kwin_output_config: Path, output: str = "eDP-1") -> float | None:
    """KDE's scale for an output from ~/.config/kwinoutputconfig.json (None if unknown)."""
    try:
        data = json.loads(kwin_output_config.read_text())
    except (OSError, ValueError):
        return None
    for section in data if isinstance(data, list) else ():
        if isinstance(section, dict) and section.get("name") == "outputs":
            for entry in section.get("data", ()):
                if entry.get("connectorName") == output and isinstance(entry.get("scale"), (int, float)):
                    return float(entry["scale"])
    return None


def kde_strip_width(left_reserve: int, hypr_scale: str, kde: float | None) -> int:
    """Logical width in KDE covering the same physical pixels as left_reserve in Hyprland."""
    try:
        hypr = float(hypr_scale)
    except ValueError:   # panel_scale = "auto": Hyprland's scale is not known here
        return left_reserve
    if not kde or kde <= 0:
        return left_reserve
    return max(1, round(left_reserve * hypr / kde))


def kde_strip_unit(marker: str, width: int, output: str = "eDP-1") -> str:
    return (f"# {marker}. Black strip over the panel's defective left edge in KDE sessions\n"
            "# (the Hyprland session has it in its own Waybar).\n"
            "[Unit]\nDescription=Black strip over the internal panel's left edge (KDE)\n"
            "PartOf=graphical-session.target\nAfter=graphical-session.target\n"
            "ConditionEnvironment=XDG_CURRENT_DESKTOP=KDE\n\n"
            f"[Service]\nExecStart=%h/.local/bin/t2-leftstrip {int(width)} {output}\n"
            "Restart=on-failure\nRestartSec=3\n\n"
            "[Install]\nWantedBy=graphical-session.target\n")


KDE_KEYS_UNIT = "t2-kde-keys.service"
BRIGHTNESS_STEPS = (("down", "-5", "Screen brightness down (dark at the minimum)"), ("up", "+5", "Screen brightness up"))


def brightness_entry(marker: str, home: str, step: str, name: str) -> str:
    """Menu entry the KDE brightness key launches (t2-kde-keys binds it)."""
    return (f"[Desktop Entry]\n# {marker}: KDE brightness key, as in Hyprland (hypr-brightness)\n"
            f"Type=Application\nName={name}\nExec={home}/.local/bin/hypr-brightness screen {step}\n"
            # no launch feedback: without it KDE bounces a generic app icon at the cursor on
            # every key press (the key runs this entry like an app start)
            "Icon=display-brightness\nStartupNotify=false\n"
            "NoDisplay=true\nX-KDE-GlobalAccel-CommandShortcut=true\n")


def kde_keys_unit(marker: str) -> str:
    return (f"# {marker}. KDE sessions: brightness keys through hypr-brightness (t2-kde-keys).\n"
            "[Unit]\nDescription=KDE brightness keys as in Hyprland (backlight off at the minimum)\n"
            "After=plasma-workspace.target\nConditionEnvironment=XDG_CURRENT_DESKTOP=KDE\n\n"
            "[Service]\nType=oneshot\nExecStart=%h/.local/bin/t2-kde-keys\n\n"
            "[Install]\nWantedBy=plasma-workspace.target\n")
