# What the deploy never touches

This laptop boots from an encrypted disk with a customized T2 initramfs (the keyboard has to work
before the disk is unlocked). Breaking that means a machine that doesn't boot, so the repository
keeps a strict no-go list. The full rule is
[`.kiro/steering/protected-system-boundary.md`](../.kiro/steering/protected-system-boundary.md).

## The protected boundary

No task, helper or package install may change:

- LUKS/cryptsetup and LVM: configuration, keys, unlock hooks, volumes;
- `/etc/fstab`, `/etc/crypttab`, swap and resume;
- kernels, modules, headers, the bootloader and its configuration;
- the initramfs and everything that generates it.

The deploy doesn't run `update-initramfs`, `update-grub` (with one exception, below),
`grub-install` or kernel module builds, and doesn't unload or replace T2 drivers. It never runs
`apt autoremove` or a full upgrade. Your normal system updates are yours; there are no apt holds.

That's also why some features are manual runbooks instead of tasks: growing swap for hibernate
([hibernate-swap.md](hibernate-swap.md)) and verbose boot ([verbose-boot.md](verbose-boot.md)).

## The package guard

Every apt install goes through `manage.packages.install_packages`. Before anything runs as root:

1. `apt-get --simulate` plans the install. A plan that removes anything is refused.
2. Snap, snapd, Flatpak and their plugins are refused, whether requested or pulled in.
3. Protected packages are refused: kernels, GRUB, shim, initramfs tools, cryptsetup, LVM, DKMS,
   kmod, udev, systemd, firmware, `apple-*` and `t2-*` packages, PipeWire, WirePlumber and ALSA
   UCM.
4. Every planned `.deb` is downloaded and unpacked. Its file paths may not land in `/boot`,
   module directories, initramfs, GRUB, cryptsetup, LVM or modprobe locations, and its
   maintainer scripts may not call `update-initramfs`, `update-grub`, `cryptsetup` and the like.

The sudo helper repeats all checks right before it installs. An apt preference
(`files/apt/90-t2-package-policy.pref`) pins snapd and flatpak to -1 as well.

Snap and Flatpak are blocked on purpose. They pull in dependencies nobody here controls, and some
packages are built poorly for this kind of setup; Chromium as a Snap drags in GNOME pieces, for
example. Everything comes from Ubuntu's archive, a vendor's signed apt repository, or a pinned
and checksummed upstream release.

Two workarounds follow from the guard. Xfe's package conflicts with `im-config`, which KDE needs,
so `tasks/xfe.py` unpacks the verified Ubuntu package into `/usr/local` instead of installing it.
Intel VTune is blocked because its install script builds and loads kernel modules.

## The one exception: CPU mitigations

The owner approved one boot change: `cpu_mitigations_off = true` makes `tasks/cpu_mitigations.py`
write a single GRUB drop-in (`/etc/default/grub.d/90-t2-mitigations.cfg`) that adds
`mitigations=off`. Only when that file changes does it back up `/boot/grub/grub.cfg` and run
`update-grub`. `/etc/default/grub`, kernels, initramfs and every other boot option stay as they
are. Setting it back to `false` removes the drop-in the same way. Details and the trade-off:
[cpu-mitigations.md](cpu-mitigations.md).

## Root changes are small and visible

Run with `--dry` first; it lists every change, including the ones that need sudo. Most of the
deploy runs as your user and writes into your home directory. The system files it writes are
mostly drop-ins under `/etc`: udev rules, sysctl and tmpfiles snippets, apt sources, keys and
preferences, sshd and fail2ban drop-ins, a few systemd units and AppArmor profiles.

## If you fork

Keep the guard. If your machine has a different boot setup, read the protected list in
`manage/packages.py` (`_PROTECTED`, `_PROTECTED_PATHS`) and extend it before you add packages.
