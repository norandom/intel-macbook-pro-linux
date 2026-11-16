# Known issues

Defects we know about, with what we saw, the cause as far as we know it, and the sources.

## Hibernate hangs the machine (T2 driver limitation)

Status: cause found, fix in testing (2026-11-16). Machine: MacBookPro16,1, Ubuntu 26.04, kernel 7.3.4-3-t2.

What happens: after Hibernate the screen locks, then the machine freezes with the display on. It
never powers off, and a forced power-off is needed. The journal of that boot ends with:

```
kernel: PM: hibernation: hibernation entry
kernel: Filesystems sync: 0.048 seconds
```

Nothing after that point reaches the disk, so the hang is in the next phase: freezing tasks and
devices to create the memory image.

Narrowed down with the kernel's `pm_test` (`~/t2-tests/test3.sh`, 2026-11-16): the `freezer` and
`devices` stages pass, with and without the Wi-Fi driver, so the T2 bridge (`t2bce_*`), Wi-Fi and
the AMD GPU all freeze cleanly. The hang is in the `platform` stage, where the kernel calls the
firmware's ACPI S4 (hibernate) methods. Apple's EFI firmware doesn't implement that for Linux.

So the community workaround (unloading the T2 bridge driver before sleep) isn't needed here, and
on the current `t2bce` stack it's discouraged anyway: the driver saves and restores its own state,
and unloading it is what used to break sleep.

Fix in testing: disk mode `shutdown` instead of `platform` (`HibernateMode=shutdown` in
`/etc/systemd/sleep.conf.d/t2-hibernate.conf`, set by the `hibernate` config flag). The kernel
writes the image and powers off without the firmware call; the next boot restores it. Status:
waiting for `test3.sh shutdown` to pass all stages before `hibernate = true`.

Sources:

- t2-suspend-fix (kernel 7.2, t2bce): the T2 driver is no longer unloaded before sleep; it saves
  and restores its state natively: https://github.com/cairolidavide/t2-suspend-fix

- t2linux wiki, post-install guide, suspend workaround (unload/reload the T2 bridge driver):
  https://wiki.t2linux.org/guides/postinstall/
- t2linux/T2-Ubuntu issue #195, MacBookPro15,1: suspend/resume crashes; apple-bce couldn't be
  unloaded at sleep time and the dying T2 controller took keyboard and trackpad with it:
  https://github.com/t2linux/T2-Ubuntu/issues/195
- CachyOS forum: from kernel 7.2 `apple_bce` became `t2bce_dma`, `t2bce_core` and `t2bce_vhci`,
  so older workarounds that name `apple_bce` no longer match:
  https://discuss.cachyos.org/t/macbook-air-t2-doesnt-work-with-the-latest-cachyos-lts-kernel-is-there-any-fix/35559
- Owner's machine: `journalctl -b -1` of the boot that hung (2026-11-16 12:03).
