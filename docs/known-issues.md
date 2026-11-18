# Known issues

Defects we know about, with what we saw, the cause as far as we know it, and the sources.

## Overnight deep suspend loses the session — unresolved (2026-11-18)

The owner selected Suspend from the menu while plugged in. The previous boot ends
on 2026-11-17 at 21:18:30 CET with `PM: suspend entry (deep)`; the next boot starts
on 2026-11-18 at 08:20:47 CET. Starting with the power button produced the startup
chime. This was a fresh boot, not merely a restarted Hyprland session. There is no
recorded suspend exit or orderly shutdown, and systemd-pstore found no stored report.
The evidence does not establish whether entry, overnight sleep, or resume failed.

Ordinary suspend remains unresolved. Hibernate is a separate, previously tested
path (below); use that for overnight sleep pending an owner-run controlled suspend
and resume test. Do not apply legacy apple-bce unload hooks to the current t2bce
stack, or change boot/kernel settings based only on this incident.

## Windows restored from the tab bar stay on top of everything - fixed

Status: fixed in `hypr-windows`, 2026-11-16 (tested live: overlay closed, window back on its
workspace, focused and on top).

What happens: after minimizing a window (title-bar button) and bringing it back from the tab
bar, it stays above every other window. Clicking another window, or its title bar, doesn't bring
that one forward, and its contents (terminal tabs) don't react. Only the tab bar seems to work.
Windows that were never minimized behave normally.

Cause: minimize moves the window to the hidden workspace `special:minimized`. The tab bar's
"activate" only focused it there, which opens that special workspace as an overlay. Hyprland
always draws special workspaces above the normal one, so the window was still minimized, just
shown on a layer nothing on the desktop can get above. Fix: the window worker moves a minimized
window back to the normal workspace as soon as it gets focus, and closes the overlay.

## Title bars: click doesn't raise, double-click doesn't unmaximize - fix pending verification

Status: patched build ready, 2026-11-16, not yet confirmed on the machine (Hyprland 0.53.3, hyprland-plugin-hyprbars 0.53.0-1).

What happens: clicking a window's title bar doesn't bring it to the front, double-clicking the
bar of a maximized window often does nothing, and a dragged window can stay on the pointer.

Cause: in hyprbars 0.53.0 the focused window's bar accepts any click inside its own area, even
where another window covers it. Windows open centred, so bars overlap often, and the click goes
to the window below. A release was only handled while the bar's window had focus, so a missed
release left the bar armed: the next click was eaten or the drag never ended. Upstream fixed both
in hyprland-plugins `f2747deb` (#722, 2026-11-15) and earlier commits, but only for newer
Hyprland. We backport the two fixes as a patch and build the plugin in the deploy
(`files/desktop/hyprbars/`).

Sources: https://github.com/hyprwm/hyprland-plugins/pull/722,
https://github.com/hyprwm/hyprland-plugins/commits/main/hyprbars/barDeco.cpp

## Hibernate hangs the machine (T2 driver limitation) - fixed

Status: fixed, 2026-11-16. A real hibernate and restore worked with keyboard, trackpad and audio
back (T2 drivers unloaded 13:00:57, loaded again after the restore 13:02:02). Machine: MacBookPro16,1, Ubuntu 26.04, kernel 7.3.4-3-t2.

What happens: after Hibernate the screen locks, then the machine freezes with the display on. It
never powers off, and a forced power-off is needed. The journal of that boot ends with:

```
kernel: PM: hibernation: hibernation entry
kernel: Filesystems sync: 0.048 seconds
```

Nothing after that point reaches the disk, so the hang is in the next phase: freezing tasks and
devices to create the memory image.

Narrowed down with the kernel's `pm_test` ([`t2-tests/test3.sh`](t2-tests/README.md), 2026-11-16): the `freezer` and
`devices` stages pass, with and without the Wi-Fi driver, so the T2 bridge (`t2bce_*`), Wi-Fi and
the AMD GPU all freeze cleanly. The hang is in the `platform` stage, where the kernel calls the
firmware's ACPI S4 (hibernate) methods. Apple's EFI firmware doesn't implement that for Linux.

For suspend, the community workaround (unloading the T2 bridge driver) isn't needed and on the
`t2bce` stack it's discouraged: the driver keeps its state across suspend. Hibernate is different,
see below.

Fix, part 1: disk mode `shutdown` instead of `platform` (`HibernateMode=shutdown` in
`/etc/systemd/sleep.conf.d/t2-hibernate.conf`). The kernel writes the image and powers off
without the firmware call. `test3.sh shutdown` passed all five stages.

Then the first real hibernate restored the session, but keyboard and trackpad were dead, and
the machine looped back into that state on every power-on until the image was gone. With the
Mac really off, the T2 chip is power-cycled; the restored kernel still has the driver state from
before, which no longer matches. This is the case the community workaround is for.

Fix, part 2: `t2-hibernate-bce.service` unloads the T2 bridge drivers before hibernate (PipeWire
stopped first, no force; if they won't unload, hibernate is cancelled) and loads them fresh after
the restore. `test4.sh` showed the unload and reload work in a running session with every device
coming back. The real hibernate then restored the session with every device working; closing
the lid now hibernates (`lid_close = "hibernate"`) on the owner's machine.

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
