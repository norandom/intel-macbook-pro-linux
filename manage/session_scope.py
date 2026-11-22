"""Keep Hyprland services out of KDE, and give KDE the same black left strip.

The Ubuntu packages of waybar, mako, hypridle and hyprpolkitagent enable themselves for every
graphical session (/etc/systemd/user/graphical-session.target.wants, package-owned). A KDE
login reaches that target too, so the Hyprland bar, notifications, idle rules (hyprctl dpms,
dim, lock) and polkit agent came up inside Plasma. A per-user drop-in limits them to
Hyprland sessions; the package links stay untouched.

The black strip over the panel's defective left edge (desktop_left_reserve) is a Waybar
layer-shell bar in Hyprland. KWin supports layer-shell too, so KDE runs the same strip as
its own Waybar, sized to cover the same physical pixels at KDE's scale.
"""
import json
from pathlib import Path

HYPRLAND_ONLY = ("waybar.service", "mako.service", "hypridle.service", "hyprpolkitagent.service")
DROPIN = "t2-hyprland-only.conf"
KDE_STRIP_UNIT = "t2-kde-leftstrip.service"
KDE_STRIP_CONFIG = "leftstrip-kde.jsonc"


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


def kde_strip_config(marker: str, width: int, output: str = "eDP-1") -> str:
    bar = {"output": output, "name": "leftstrip", "layer": "top", "position": "left",
           "width": width, "exclusive": True, "spacing": 0,
           "modules-left": ["custom/strip"], "modules-center": [], "modules-right": [],
           "custom/strip": {"format": " ", "tooltip": False}}
    return f"// {marker}: black strip over the panel's defective left edge (KDE session)\n" + json.dumps(bar, indent=2) + "\n"


def kde_strip_unit(marker: str) -> str:
    return (f"# {marker}. Black strip over the panel's defective left edge in KDE sessions\n"
            "# (the Hyprland session has it in its own Waybar).\n"
            "[Unit]\nDescription=Black strip over the internal panel's left edge (KDE)\n"
            "PartOf=graphical-session.target\nAfter=graphical-session.target\n"
            "ConditionEnvironment=XDG_CURRENT_DESKTOP=KDE\n\n"
            "[Service]\nExecStart=/usr/bin/waybar -c %h/.config/waybar/" + KDE_STRIP_CONFIG
            + " -s %h/.config/waybar/style.css\nRestart=on-failure\nRestartSec=3\n\n"
            "[Install]\nWantedBy=graphical-session.target\n")
