"""The Hyprland keyboard policy (files/desktop/hypr/input.conf) and two desktops in KDE.

German Apple layout without dead keys plus US, the same XKB options (Caps Lock = Compose, both
Shifts cancel Caps Lock, Right Option = Super, Left Option = Mac Option for @ [ ] { } | \\ EUR ~),
key repeat 40/s after 250 ms, NumLock on. Only these keys are written (kwriteconfig6); the rest
of kxkbrc/kcminputrc stays KDE's and yours. tests/test_kde_input.py keeps them equal to
input.conf.
"""
from shlex import quote

LAYOUTS = ("de", "us")
VARIANTS = ("mac_nodeadkeys", "")
OPTIONS = ("compose:caps", "shift:both_capslock_cancel", "altwin:swap_ralt_rwin", "lv3:lalt_switch")
REPEAT_RATE = 40
REPEAT_DELAY = 250

# (file, group, key, value)
SETTINGS = (
    ("kxkbrc", "Layout", "Use", "true"),
    ("kxkbrc", "Layout", "LayoutList", ",".join(LAYOUTS)),
    ("kxkbrc", "Layout", "VariantList", ",".join(VARIANTS)),
    ("kxkbrc", "Layout", "DisplayNames", ","),
    ("kxkbrc", "Layout", "Options", ",".join(OPTIONS)),
    ("kxkbrc", "Layout", "ResetOldOptions", "true"),
    ("kxkbrc", "Layout", "SwitchMode", "Global"),
    ("kcminputrc", "Keyboard", "RepeatRate", str(REPEAT_RATE)),
    ("kcminputrc", "Keyboard", "RepeatDelay", str(REPEAT_DELAY)),
    ("kcminputrc", "Keyboard", "KeyRepeat", "repeat"),
    ("kcminputrc", "Keyboard", "NumLock", "0"),   # 0 = turn on at login
    # Two virtual desktops, as Hyprland's workspaces.conf (KWin adds the second desktop's id)
    ("kwinrc", "Desktops", "Number", "2"),
    ("kwinrc", "Desktops", "Rows", "1"),
)


def apply_script() -> str:
    """Write the settings when they differ; then tell a running KDE session to reload them."""
    lines = ["set -eu", "command -v kwriteconfig6 >/dev/null || exit 0", "changed="]
    for file, group, key, value in SETTINGS:
        lines.append(f'[ "$(kreadconfig6 --file {file} --group {group} --key {key})" = {quote(value)} ] || '
                     f'{{ kwriteconfig6 --file {file} --group {group} --key {key} {quote(value)}; changed=1; }}')
    # a running KDE session: create the second desktop now (KWin saves it in kwinrc itself)
    lines += ['n=$(qdbus6 org.kde.KWin /VirtualDesktopManager org.freedesktop.DBus.Properties.Get '
              'org.kde.KWin.VirtualDesktopManager count 2>/dev/null || echo 2)',
              '[ "$n" -ge 2 ] || qdbus6 org.kde.KWin /VirtualDesktopManager '
              'org.kde.KWin.VirtualDesktopManager.createDesktop 1 "Desktop 2" >/dev/null 2>&1 || true',
              '[ -n "$changed" ] || exit 0',
              'echo "KDE keyboard and desktop settings updated"',
              "# a running KDE session picks them up now (KWin owns the keyboard on Wayland)",
              "dbus-send --session --type=signal /Layouts org.kde.keyboard.reloadConfig 2>/dev/null || true",
              "dbus-send --session --type=signal /Keyboard org.kde.keyboard.reloadConfig 2>/dev/null || true"]
    return "\n".join(lines) + "\n"
