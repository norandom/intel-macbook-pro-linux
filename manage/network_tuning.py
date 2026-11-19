"""Sender-side TCP tuning (config network_tuning): the managed values and the kernel defaults."""
from __future__ import annotations

DEST = "/etc/sysctl.d/61-t2-network.conf"
# key -> (managed value, kernel default restored when network_tuning = false)
SETTINGS = {
    "net.ipv4.tcp_congestion_control": ("bbr", "cubic"),
    "net.ipv4.tcp_slow_start_after_idle": ("0", "1"),
    "net.ipv4.tcp_mtu_probing": ("1", "0"),
}


def parse(text: str) -> dict[str, str]:
    """key -> value of a sysctl.d file (comments and blank lines ignored)."""
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith(("#", ";")):
            key, _, value = line.partition("=")
            out[key.strip()] = value.strip()
    return out


def verify_commands() -> list[str]:
    return [f'test "$(sysctl -n {key})" = {managed}' for key, (managed, _default) in SETTINGS.items()]


def restore_commands() -> list[str]:
    return [f"sysctl -w {key}={default}" for key, (_managed, default) in SETTINGS.items()]
