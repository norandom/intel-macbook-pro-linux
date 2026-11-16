# Known issues

Defects we know about, with what we saw, the cause as far as we know it, and the sources.

## Hibernate hangs the machine (T2 driver limitation)

Status: open, 2026-11-16. Machine: MacBookPro16,1, Ubuntu 26.04, kernel 7.3.4-3-t2.

What happens: after Hibernate the screen locks, then the machine freezes with the display on. It
never powers off, and a forced power-off is needed. The journal of that boot ends with:

```
kernel: PM: hibernation: hibernation entry
kernel: Filesystems sync: 0.048 seconds
```

Nothing after that point reaches the disk, so the hang is in the next phase: freezing tasks and
devices to create the memory image.

Cause, as far as known: the T2 bridge drivers (`t2bce_dma`, `t2bce_core`, `t2bce_vhci`,
`t2bce_audio`; older kernels called this driver `apple-bce`) don't support the hibernation freeze.
Keyboard, trackpad, Touch Bar and audio all hang off that bridge, so when it stops, the machine
stops responding. Suspend to RAM works here; it uses different driver callbacks.

The workaround the t2linux community documents for sleep problems is a systemd sleep hook that
unloads the T2 bridge driver before sleeping and loads it again afterwards. This repository
doesn't do that: unloading T2 hardware drivers is on the protected list
([safety.md](safety.md)), and reports exist where the unload fails or the T2 devices don't come
back.

What's in place: swap is big enough (80 GiB, [hibernate-swap.md](hibernate-swap.md)) and the
`hibernate` config flag exists (polkit rule, guarded menu entry), but it stays `false`. Use
Suspend. Revisit with a newer t2 kernel; the test is one click on Hibernate with
`hibernate = true`.

Sources:

- t2linux wiki, post-install guide, suspend workaround (unload/reload the T2 bridge driver):
  https://wiki.t2linux.org/guides/postinstall/
- t2linux/T2-Ubuntu issue #195, MacBookPro15,1: suspend/resume crashes; apple-bce couldn't be
  unloaded at sleep time and the dying T2 controller took keyboard and trackpad with it:
  https://github.com/t2linux/T2-Ubuntu/issues/195
- CachyOS forum: from kernel 7.2 `apple_bce` became `t2bce_dma`, `t2bce_core` and `t2bce_vhci`,
  so older workarounds that name `apple_bce` no longer match:
  https://discuss.cachyos.org/t/macbook-air-t2-doesnt-work-with-the-latest-cachyos-lts-kernel-is-there-any-fix/35559
- Owner's machine: `journalctl -b -1` of the boot that hung (2026-11-16 12:03).
