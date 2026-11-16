# Protected system boundary: strict no-go

Explicit owner instruction: do not touch cryptsetup, fstab or the kernels.
This T2 install has substantial customizations for keyboard presence during
initramfs and LVM/LUKS decryption. Desktop/tool provisioning must fit around them.

## Forbidden mutations

No repository deploy, helper, installer, package transaction, cleanup tool or
rollback may modify, replace, remove, upgrade, regenerate or reconfigure:

- cryptsetup/LUKS configuration, encryption metadata, keys, unlock hooks or flows;
- LVM configuration, volumes, mappings or activation/decryption setup;
- /etc/fstab, /etc/crypttab, swap/resume configuration and related boot mounts;
- installed kernels, kernel images/modules/headers, linux-t2 or generic fallback
  kernels, kernel selection or bootloader configuration;
- initramfs/mkinitcpio/mkinitio configuration, hooks, keyboard-presence setup or
  generated initramfs/boot artifacts, regardless of the installed generator.

Do not run update-initramfs, mkinitcpio, dracut regeneration, update-grub,
grub-install, kernel/module rebuilds or related package hooks. Do not unload,
blacklist or replace existing T2 hardware drivers. No autoremove, full upgrade,
root remount, disk swap recreation or changes to encrypted storage.

## Package and build constraints

Package preflight must reject protected package installs/upgrades/removals,
replacements, and maintainer-script/trigger paths that regenerate or reconfigure
protected boot/storage state. A simulated package list alone is insufficient
when maintainer scripts/triggers are unknown. Report a blocked plan rather than
execute it. Preserve normal owner-managed system upkeep outside this project;
this project does not impose apt holds or rewrite update policy.

Building a userspace compositor does not authorize changes to the kernel,
DKMS, initramfs, bootloader, encryption or storage. Use a compatible isolated
userspace build; if prerequisites cross this boundary, report the incompatibility.
Rollback is equally constrained: it must never restore/rewrite protected files.

Read-only inventory or hashes may document the baseline where accessible;
do not expose encryption keys or confidential decryption configuration. Lack of
read access is a reported verification gap, never a reason to escalate for
modification. Existing GPU power configuration remains untouched pending capture.

## Owner-approved exception: CPU mitigations switch (2026-11-16)

The owner explicitly asked for a config flag to turn the kernel's CPU security mitigations
off (single-user workstation, performance first). Allowed, and only this:

- `tasks/cpu_mitigations.py` (config `cpu_mitigations_off`) writes or removes one file,
  `/etc/default/grub.d/90-t2-mitigations.cfg`, which appends `mitigations=off` to
  `GRUB_CMDLINE_LINUX_DEFAULT`. `/etc/default/grub` itself is never edited.
- When, and only when, that drop-in changes, it backs up `/boot/grub/grub.cfg` and runs
  `update-grub` (the same regeneration every kernel update already performs).
- Kernels, initramfs, LUKS/LVM, fstab, keyboard-presence setup and all other boot options stay
  untouched. Any further boot change needs a new explicit owner decision.
