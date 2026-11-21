"""Apps that draw their own title bar get no hyprbars bar on top (config own_titlebar_apps).

GTK3 on Wayland always draws a client-side title bar, and Tauri/tao apps (e.g. Deckle) put
their own header bar there, which neither CSS nor an environment variable removes cleanly.
Running them under XWayland drops that bar but forces whole-number scaling (2x on a 1.6
panel: too big). So these windows keep their own bar and Hyprland draws none.
"""
import re

_CLASS = re.compile(r"[A-Za-z0-9_.-]+\Z")


def conf(classes) -> str:
    """Hyprland window rules for the given window classes (exact match)."""
    if not isinstance(classes, list) or not all(isinstance(c, str) and _CLASS.match(c) for c in classes):
        raise RuntimeError(f'config.toml own_titlebar_apps must be a list of window classes like ["Deckle"]: {classes!r}')
    return "".join(f"windowrule = match:class ^({re.escape(c)})$, hyprbars:no_bar on\n" for c in classes)
