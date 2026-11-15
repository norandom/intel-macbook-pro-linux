"""Pure helpers for tasks/resource_policy.py (importable without pyinfra side effects)."""

import re
import subprocess

TURBO_SYSFS = "/sys/devices/system/cpu/intel_pstate/no_turbo"
# Stable path the shell-user-tools feature sources; never edits shell startup files.
TURBO_FRAGMENT = "~/.config/t2-mac-kde/turbo.bash"

INOTIFY_INSTANCES_FLOOR = 1024

# earlyoom matches --avoid/--prefer against /proc/PID/comm (max 15 chars).
# Source VM list plus the KDE/Plasma session observed on this laptop. --avoid is a
# score bias, not immunity. Source --prefer (browsers/electron) is rejected.
AVOID_COMMS = (
    "init", "systemd", "sshd", "agetty",
    "Hyprland", "hyprland", "waybar", "mako", "hypr-rdp", "uwsm",
    "pipewire", "pipewire-pulse", "wireplumber",
    "plasmashell", "kwin_wayland", "kwin_wayland_wr", "kwin_x11", "ksmserver",
    "kded6", "startplasma-way", "startplasma-x11", "sddm", "sddm-helper",
    "Xwayland", "xdg-desktop-por",
)


def avoid_regex(comms=AVOID_COMMS) -> str:
    for comm in comms:
        if len(comm) > 15:
            raise ValueError(f"comm name longer than 15 chars never matches: {comm}")
    return "(^|/)(" + "|".join(re.escape(c) for c in comms) + ")$"


def earlyoom_defaults() -> str:
    """Content for /etc/default/earlyoom (source -m 5 -s 10 -r 3600, no --prefer)."""
    return (
        "# Managed by t2-mac-kde (laptop-resource-policy).\n"
        "# Act when available RAM < 5% AND free swap (disk + zram) < 10%; SIGKILL at half.\n"
        "# Desktop/session processes (KDE and Hyprland) are deprioritized, not immune.\n"
        "# Source browser --prefer rejected: no evidence browsers should die first.\n"
        f"EARLYOOM_ARGS=\"-m 5 -s 10 -r 3600 --avoid '{avoid_regex()}'\"\n"
    )


def inotify_instances_target(current: int | None) -> int:
    """Adopt-floor: never lower an existing larger value."""
    if current is None:
        return INOTIFY_INSTANCES_FLOOR
    return max(current, INOTIFY_INSTANCES_FLOOR)


def limits_sysctl(current: int | None) -> str:
    return ("# Managed by t2-mac-kde (laptop-resource-policy)\n"
            f"fs.inotify.max_user_instances = {inotify_instances_target(current)}\n")


def coredump_applicable(core_pattern: str) -> bool:
    """systemd-coredump limits apply only when it is the active crash handler."""
    return "systemd-coredump" in core_pattern


def read_int(path: str) -> int | None:
    try:
        with open(path) as handle:
            return int(handle.read().strip())
    except (OSError, ValueError):
        return None


def read_text(path: str) -> str:
    try:
        with open(path) as handle:
            return handle.read()
    except OSError:
        return ""


def unit_state(unit: str) -> str:
    """systemctl is-enabled output ('' when systemctl is unavailable)."""
    try:
        result = subprocess.run(["systemctl", "is-enabled", unit],
                                capture_output=True, text=True, check=False)
    except OSError:
        return ""
    return result.stdout.strip()


def unit_active(unit: str) -> bool:
    try:
        return subprocess.run(["systemctl", "is-active", "--quiet", unit], check=False).returncode == 0
    except OSError:
        return False


def unit_installed(state: str) -> bool:
    return state not in ("", "not-found") and "No such file" not in state
