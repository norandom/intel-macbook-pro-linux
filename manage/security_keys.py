"""Security keys (YubiKey, FIDO2/U2F): packages, pam_u2f as an alternative to the password.

pam_u2f is added as a pam-auth-update profile (the same mechanism Ubuntu's fingerprint login
uses), only when config yubikey_login = true and a key is registered. It is "sufficient": with
no key, or no touch, the password still works. Only the services in SERVICES ask for the key;
SSH, cron and the rest keep password-only PAM. Key handles live in a root-owned file, so
nothing running as the user can add a key for itself.
"""
PACKAGES = ("yubikey-manager", "libpam-u2f", "pcscd")
PROFILE_NAME = "t2-u2f"
PROFILE = f"/usr/share/pam-configs/{PROFILE_NAME}"
MAPPINGS = "/etc/t2-mac-kde/u2f_mappings"
STAGED = "~/.config/t2-mac-kde/u2f_keys"     # written by t2-yubikey register / add-spare
ORIGIN = "pam://t2-mac-kde"   # fixed, so a hostname change doesn't orphan the keys
SERVICES = ("sudo", "sudo-i", "su", "polkit-1", "sddm", "login", "hyprlock")


def profile() -> str:
    services = ":".join(SERVICES)
    return (
        "Name: Security key (YubiKey via pam_u2f) instead of the password (t2-mac-kde)\n"
        "Default: no\n"
        "Priority: 260\n"
        "Auth-Type: Primary\n"
        "Auth:\n"
        f"\t[success=1 default=ignore]\tpam_succeed_if.so quiet service notin {services}\n"
        f"\t[success=end default=ignore]\tpam_u2f.so cue nouserok origin={ORIGIN} appid={ORIGIN} authfile={MAPPINGS}\n"
    )


def mapping_lines(text: str, user: str) -> list[str]:
    """Valid pam_u2f mapping lines for `user` (user:keyHandle,pubkey,...[:more keys])."""
    out = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith(f"{user}:") and line.count(",") >= 1 and len(line) > len(user) + 10:
            out.append(line)
    return out


def key_count(line: str) -> int:
    return len(line.split(":")[1:]) if line else 0
