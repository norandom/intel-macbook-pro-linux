"""Chromium/Electron apps pick their password backend from XDG_CURRENT_DESKTOP; they know
KDE and GNOME but not Hyprland, fall back to "basic"/"portal" and warn. User desktop-entry
overrides add --password-store=<backend> so Hyprland uses the same wallet as KDE does.

The browsers' entries also turn on VA-API video decoding on the Intel GPU (VIDEO_FLAGS): without
it Chromium decodes YouTube on the CPU (2026-11-25: ~125% CPU, 31 W, fans at full speed).
"""
import re

APPS = ("vivaldi-stable.desktop", "chromium.desktop", "code.desktop", "positron.desktop",
        "slack.desktop", "discord.desktop", "md.obsidian.Obsidian.desktop", "bitwarden.desktop")
MARK = "X-T2-Password-Store"
# YouTube steered off AV1 (UHD 630 has no AV1 decoder, so AV1 is always CPU): enhanced-h264ify
# (Chrome Web Store, open source), force-installed by policy into both browsers.
H264IFY = "omkfmpieigblcllmkgbflkikinpkodlk"
POLICY = {"ExtensionInstallForcelist": [f"{H264IFY};https://clients2.google.com/service/update2/crx"]}
POLICY_DIRS = ("/etc/vivaldi/policies/managed", "/etc/chromium/policies/managed")
# Chromium-based browsers: hardware video decoding through VA-API (Intel iHD driver) on Wayland.
VIDEO_APPS = ("vivaldi-stable.desktop", "chromium.desktop")
VIDEO_FLAGS = ("--enable-features=AcceleratedVideoDecodeLinuxGL,AcceleratedVideoDecodeLinuxZeroCopyGL",)


def override(text: str, store: str, extra: tuple = ()) -> str:
    """Add --password-store (if store) and extra flags to every Exec= line (before field codes like %U)."""
    flags = ((f"--password-store={store}",) if store else ()) + tuple(extra)
    out = []
    for line in text.splitlines():
        if line.startswith("Exec="):
            m = re.match(r"(Exec=\S+)(.*)", line)
            missing = [f for f in flags if f.split("=", 1)[0] + "=" not in m.group(2)]
            if missing:
                line = f"{m.group(1)} {' '.join(missing)}{m.group(2)}"
        out.append(line)
    body = "\n".join(out)
    return body.replace("[Desktop Entry]", f"[Desktop Entry]\n{MARK}={store}", 1) + "\n"
