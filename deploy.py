"""Full workstation deploy, @local only, as the desktop user (sudo for system parts).

    .venv/bin/pyinfra @local deploy.py --use-sudo-password

Each task file also runs on its own, e.g. `.venv/bin/pyinfra @local tasks/fonts.py`.
"""
from pyinfra import local
from manage.preflight import validate_local_context

validate_local_context()
for task in (
    "node",             # nvm + Node/npm (user)
    "tools",            # snap/flatpak pin + core CLI packages
    "resource_policy",  # turbo, zram, earlyoom, journald/coredump limits
    "storage_health",   # smartd + daily NVMe check, alerts in new shells
    "remote_access",    # tailscale, sshd at boot, fail2ban, RDP firewall
    "containers",       # rootless podman, docker compat, compose, podman-tui
    "fonts",            # nerd fonts, fixedsys, fontconfig
    "apps",             # application suite + release tools
    "xfe",              # Xfe file manager (unpacked; keeps KDE's im-config)
    "shell",            # bash/grml, history, nvim-simple, npm/uv user tools
    "themes",           # five palettes + hypr-termtheme
    "desktop",          # Hyprland session, waybar, decorations, night filter
    "rdp",              # hypr-rdp inside the Hyprland session
):
    local.include(f"tasks/{task}.py")
