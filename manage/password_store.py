"""Chromium/Electron apps pick their password backend from XDG_CURRENT_DESKTOP; they know
KDE and GNOME but not Hyprland, fall back to "basic"/"portal" and warn. User desktop-entry
overrides add --password-store=<backend> so Hyprland uses the same wallet as KDE does.
"""
import re

APPS = ("vivaldi-stable.desktop", "chromium.desktop", "code.desktop", "positron.desktop",
        "slack.desktop", "discord.desktop", "md.obsidian.Obsidian.desktop", "bitwarden.desktop")
MARK = "X-T2-Password-Store"


def override(text: str, store: str) -> str:
    """Append --password-store to every Exec= line (before field codes like %U)."""
    flag = f"--password-store={store}"
    out = []
    for line in text.splitlines():
        if line.startswith("Exec=") and "--password-store=" not in line:
            m = re.match(r"(Exec=\S+)(.*)", line)
            line = f"{m.group(1)} {flag}{m.group(2)}"
        out.append(line)
    body = "\n".join(out)
    return body.replace("[Desktop Entry]", f"[Desktop Entry]\n{MARK}={store}", 1) + "\n"
