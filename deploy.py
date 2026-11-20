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
    "dev_libs",         # GTK/WebKit/Ayatana build libraries (Tauri); replaces the conflicting legacy appindicator
    "fan_curve",        # earlier cooling: full fans by 85 C; CPU power policy unchanged
    "resource_policy",  # turbo, zram, earlyoom, journald/coredump limits
    "cpu_mitigations",  # config cpu_mitigations_off: GRUB drop-in (owner exception)
    "t2_pack",          # config t2_pack_pin: hold the tested T2/Hyprland versions (owner exception); .deb backup
    "storage_health",   # smartd + daily NVMe check, alerts in new shells
    "remote_access",    # tailscale, sshd at boot, fail2ban, RDP firewall
    "network_tuning",   # config network_tuning: BBR + two sender-side TCP sysctls (on by default)
    "traffic_shaping",  # config cake_upload_mbit/cake_download_mbit: CAKE shaper (off by default)
    "security_keys",    # YubiKey tools; config yubikey_login: touch the key instead of a password
    "containers",       # rootless podman, docker compat, compose, podman-tui
    "virtualization",   # virt-manager on KVM, libvirt default NAT network
    "fonts",            # nerd fonts, fixedsys, fontconfig
    "apps",             # application suite + release tools
    "vendor_apps",      # vendor repos/.debs/tarballs (before themes: editors get palettes)
    "office_apps",      # LibreOffice (tabbed UI), Craft suite, OpenIDEA
    "nix_tools",        # Nix (Ubuntu package) + pinned flake profile for user CLI tools
    "xfe",              # Xfe file manager (unpacked; keeps KDE's im-config)
    "multiplexers",      # Screen Ctrl+A keys for Zellij and Byobu
    "shell",            # bash/grml, history, nvim-simple, npm/uv user tools
    "remove_warp",      # remove the retired managed Warp trial
    "warpeer",          # Cyberterm 2077 (formerly Warpeer): pinned user-local terminal (Linux x86-64)
    "themes",           # five palettes + hypr-termtheme
    "desktop",          # Hyprland session, waybar, decorations, night filter
    "audio_effects",    # EasyEffects: QC35 3D preset, speakers bypass, BT device roles
    "speaker_dsp",      # MacBookPro16,1 speaker DSP (config speaker_dsp; off = plain speakers)
    "rdp",              # hypr-rdp inside the Hyprland session
):
    local.include(f"tasks/{task}.py")
