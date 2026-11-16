"""CPU security mitigations switch (owner exception to the protected boundary, 2026-11-16).

The only boot change this repository makes: one GRUB drop-in that appends `mitigations=off`
to the kernel command line. /etc/default/grub, kernels, initramfs and LUKS stay untouched.
"""
DROPIN = "/etc/default/grub.d/90-t2-mitigations.cfg"
GRUB_CFG = "/boot/grub/grub.cfg"
BACKUP = "/boot/grub/grub.cfg.before-t2-mitigations"
OPTION = "mitigations=off"
NOTICE_MARKER = "# {mark} t2-mac-kde cpu mitigations reboot notice"


def dropin() -> str:
    return ("# Managed by t2-mac-kde (config cpu_mitigations_off; docs/cpu-mitigations.md).\n"
            "# Sourced by grub-mkconfig after /etc/default/grub; remove + update-grub to undo.\n"
            f'GRUB_CMDLINE_LINUX_DEFAULT="${{GRUB_CMDLINE_LINUX_DEFAULT}} {OPTION}"\n')


def regenerate_commands() -> list[str]:
    """Regenerate the boot menu only when it doesn't match the setting (retries a failed run).

    Wanted: the drop-in exists (or the owner put the option in /etc/default/grub by hand).
    Present: the option is in the generated grub.cfg. On mismatch: back up, then update-grub,
    the same regeneration every kernel update performs.
    """
    return [f"want=0; {{ [ -e {DROPIN} ] || grep -qw {OPTION} /etc/default/grub; }} && want=1; "
            f"have=0; grep -qw {OPTION} {GRUB_CFG} && have=1; "
            f'if [ "$want" != "$have" ]; then cp -a {GRUB_CFG} {BACKUP} && update-grub; '
            f'else echo "boot menu already matches (mitigations off: $want)"; fi']


def notice() -> str:
    """New interactive shells: say when the running kernel doesn't match the configured state."""
    return (f'case $- in *i*) if [ -e {DROPIN} ]; then grep -qw {OPTION} /proc/cmdline || '
            f'echo "t2: CPU mitigations off is configured - reboot to apply"; '
            f'elif grep -qw {OPTION} /proc/cmdline; then '
            f'echo "t2: CPU mitigations back on is configured - reboot to apply"; fi ;; esac')
