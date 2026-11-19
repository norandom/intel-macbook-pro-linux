"""CAKE traffic shaper settings (config cake_upload_mbit / cake_download_mbit)."""
from __future__ import annotations

HELPER = "/usr/local/libexec/t2-cake"
CONF = "/etc/t2-mac-kde/cake.conf"
UNIT = "/etc/systemd/system/t2-cake.service"
RULE = "/etc/udev/rules.d/90-t2-cake.rules"
MAX_MBIT = 10000


def kbit(value, key: str) -> int:
    """Config value in Mbit/s -> kbit/s; 0 (or unset) leaves that direction unshaped."""
    if value is None:
        return 0
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be a number of Mbit/s (0 = off)")
    if value == 0:
        return 0
    if not 1 <= value <= MAX_MBIT:
        raise ValueError(f"{key} must be 0 or between 1 and {MAX_MBIT} Mbit/s")
    return int(round(value * 1000))


def conf(up_kbit: int, down_kbit: int) -> str:
    return ("# Managed by t2-mac-kde (tasks/traffic_shaping.py); read by t2-cake.\n"
            f"UP_KBIT={up_kbit}\nDOWN_KBIT={down_kbit}\n")
