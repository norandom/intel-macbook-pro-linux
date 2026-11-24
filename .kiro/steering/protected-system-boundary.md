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
this project does not impose apt holds or rewrite update policy (one opt-in exception: the
T2 pack pin, below).

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

## Owner-approved exception: T2 driver reload around hibernate (2026-11-16)

The owner explicitly asked for the t2linux community workaround after hibernate restored a
session without keyboard or trackpad (the T2 chip is power-cycled with HibernateMode=shutdown).
Allowed, and only this:

- With config `hibernate = true`, `t2-hibernate-bce.service` (RequiredBy and Before
  systemd-hibernate, -hybrid-sleep and -suspend-then-hibernate.service) runs `/usr/local/libexec/t2-hibernate-bce pre` before hibernate:
  stop PipeWire, `modprobe -r t2bce_audio t2bce_vhci t2bce_core t2bce_dma` without force; if any
  module stays loaded it reloads everything, fails (which cancels the hibernate) and suspends
  instead, so a lid-triggered hibernate never leaves the Mac running.
- After the restore (or a failed hibernate) `post` loads `t2bce_vhci` and `t2bce_audio` again
  and starts PipeWire. The reload re-creates the keyboard backlight LED, so `pre` saves its level,
  `post` writes it back and restarts `upower.service` (it keeps the removed LED open otherwise).
  Owner-approved 2026-11-24 after an independent review; no driver change. The hook also stops an
  EasyEffects started from XDG autostart before PipeWire goes down.
- Image-writing sleeps only: plain suspend, the initramfs, module options, blacklists and the drivers' files stay
  untouched. Tested by hand first (docs/t2-tests/test4.sh: unload + reload in a running session,
  all devices back). Any further driver change needs a new explicit owner decision.

## Owner-approved exception: T2 pack pin (2026-11-16)

The owner explicitly asked to pin the T2 package versions and to release this repository
against them ("in case a new version comes out we port and then release against the new T2
pack"), with .deb backups. Allowed, and only this:

- `t2-pack.toml` lists exact versions (T2 kernel metapackage + image + headers, T2 audio
  config, Apple firmware script, Hyprland + its -dev and hyprbars).
- With config `t2_pack_pin = true`, `tasks/t2_pack.py` writes one file,
  `/etc/apt/preferences.d/90-t2-pack.pref`, pinning those versions at priority 990: newer
  versions are not picked, nothing is ever downgraded (that needs > 1000). `false` removes it.
- The deploy never installs, upgrades, downgrades or removes these packages, and runs no
  kernel, initramfs or bootloader step. Moving to a new pack is an owner-run apt step after the
  manifest is bumped (docs/t2-pack.md).
- `.deb` copies of the pack go to `~/.local/share/t2-mac-kde/t2-packs/<id>` (user files, apt
  download, checked against `packs/<id>.sha256`). Any further update-policy change needs a new
  explicit owner decision.
- With config `background_updates = false` (owner request 2026-11-16, "all off"), the same task
  writes `/etc/apt/apt.conf.d/99-t2-no-background-updates` (all `APT::Periodic` jobs "0") and
  disables apt-daily, apt-daily-upgrade, update-notifier-download/-motd and
  unattended-upgrades.service. Updates then happen only when the owner runs apt. `true`
  removes the file and re-enables exactly those units.

## Owner-approved exception: earlier fan cooling (2026-11-17)

The owner requested an earlier default fan curve, prioritizing build performance
and a 90°C cooling target. `tasks/fan_curve.py` may install a userspace systemd
controller that temporarily writes the existing
`/sys/module/macsmc_hwmon/parameters/fan_control` parameter and discovered
`macsmc_hwmon` `fan*_target` sysfs files. Full fan speed is requested by 85°C.
A watchdog and stop cleanup return each fan to SMC automatic control before
restoring the runtime parameter. No driver reload, module file/options file,
kernel, initramfs or bootloader change is authorized. Live deployment remains
owner-run; `fan_curve = false` restores firmware cooling.
