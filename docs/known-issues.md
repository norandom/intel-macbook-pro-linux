# Known issues

Defects we know about, with what we saw, the cause as far as we know it, and the sources.

## Windows dragged or snapped to the right edge disappear - fixed, deploy pending (2026-11-18)

What happens: snapping a window to the right edge, or dragging it there, makes it vanish.
The pointer can also leave the screen on the right.

Cause: the RDP server keeps a virtual output (`hypr-rdp`, 1920x1080) for remote clients. With
automatic placement it sat directly right of the panel, so the desktop continued invisibly
there. A pointer at the right edge crossed onto it, and the snap then used that output.

Fix: `monitors.conf` places `hypr-rdp` apart from the panel (`-6000x0`). The pointer cannot
cross a gap, so the right edge is a real edge again. A negative x is required: automatic
placement puts the panel right of every explicitly placed output. Because the pointer cannot
return across the gap either, `hypr-windows` brings a pointer left on the virtual output back
to the screen once no remote client is connected; SUPER+SHIFT+C does it at any time.
Checked live: panel stays at 0,0, snap rectangles resolve on the panel, a stranded pointer
returns. Not checked: a remote session with the new placement.

## Taskbar clicks minimize a window instead of raising it - fixed, re-login pending (2026-11-18)

What happens: after minimizing a window from the taskbar or its title bar, clicking another
taskbar entry sometimes minimizes that window instead of bringing it forward.

Cause: Hyprland 0.53.3 never publishes a minimized state, so Waybar's `minimize-raise`
decides by the active flag alone: active entry = minimize, any other = raise. Our
`t2:minimize` dispatcher (in the patched hyprbars build) gave focus to
`workspace->getFirstWindow()`, which is the bottom of the window stack, and did not raise it.
The active window could then be one buried under others; clicking its entry to bring it
forward minimized it. Replayed with a test client that sends Waybar's requests: the toggle
itself is reliable down to 50 ms between clicks.

Fix: after parking a focused window, `t2:minimize` focuses the window used last on that
workspace (focus history, topmost as fallback) and raises it, so the active window is always
the one on top. With no window left, focus stays empty; minimizing an inactive window keeps
the current focus. No cursor warp.

The plugin compiles against the installed Hyprland headers. Deployment rebuilds it; log out
and back in afterwards (a config reload does not replace a loaded plugin at the same path).
Keyboard alternatives: SUPER+Tab cycles windows; SUPER+M opens the restore picker.

Source: [Hyprland 0.53.3 focus and workspace dispatchers](https://github.com/hyprwm/Hyprland/blob/v0.53.3/src/managers/KeybindManager.cpp),
[Waybar 0.15.0 taskbar state handling](https://github.com/Alexays/Waybar/blob/0.15.0/src/modules/wlr/taskbar.cpp).

## Overnight deep suspend loses the session — unresolved (2026-11-18)

The owner selected Suspend from the menu while plugged in. The previous boot ends
on 2026-11-17 at 21:18:30 CET with `PM: suspend entry (deep)`; the next boot starts
on 2026-11-18 at 08:20:47 CET. Starting with the power button produced the startup
chime. This was a fresh boot, not merely a restarted Hyprland session. There is no
recorded suspend exit or orderly shutdown, and systemd-pstore found no stored report.
The evidence does not establish whether entry, overnight sleep, or resume failed.

Second incident, 2026-11-22: in a KDE session, Plasma's power management suspended the idle
laptop on its own (default: sleep after 15 minutes idle) at 09:48:10; the log ends with
`PM: suspend entry (deep)` and the next boot started at 10:10:41, with no resume, panic or
pstore record. Since then the deploy sets KDE to never suspend automatically
(`powerdevilrc`: no idle suspend in any profile, lid and critical battery hibernate), the same
policy as the Hyprland session, whose idle rules never suspend.

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

## Hibernate does nothing while Bitwarden runs - fixed

Status: fixed, 2026-11-25. A real hibernate (21:32) and restore (2026-11-26 08:40) worked with
Bitwarden running.

What happened: Start -> Hibernate in KDE did nothing, with no error. The kernel had hibernation
switched off:

```
$ cat /sys/power/disk
[disabled]
$ cat /sys/power/state
freeze mem
$ busctl call org.freedesktop.login1 /org/freedesktop/login1 org.freedesktop.login1.Manager CanHibernate
s "na"
```

Kernel, boot options, swap and the resume device were the same as on the days it worked.

Cause: Bitwarden desktop (2026.10.4) keeps its vault key in `memfd_secret` memory. Such memory is
hidden even from the kernel, so it can't be written into a hibernation image, and the kernel
refuses to hibernate for as long as any process holds some (`hibernation_available()` checks
`secretmem_active()`). Bitwarden's log says `Using memfd_secret for secure key storage`. Quitting
Bitwarden brought `/sys/power/disk` back at once. Secure Boot lockdown and `nohibernate` give the
same picture and were ruled out first (`/sys/kernel/security/lockdown` was `[none]`).

Fix: with `hibernate = true` the deploy writes `~/.config/environment.d/60-t2-hibernate.conf`
with `SECURE_KEY_CONTAINER_BACKEND=keyctl`, Bitwarden's own switch for this case. The key then
lives in the kernel keyring (log: `Forcing keyctl secure key container via environment variable`).
It ends up in the hibernation image, which goes to swap on the encrypted disk. The setting
applies from the next login.

The trade-off, for the interested: `memfd_secret` memory is hidden even from the kernel, which
is the strongest of Bitwarden's three key stores and exactly why it can't be hibernated. With
`keyctl` the kernel holds the key. Other programs still can't get it by dumping Bitwarden's
memory; it is weaker only if the kernel itself is compromised (Bitwarden's source calls
`memfd_secret` "slightly better in some cases" there). While the vault is unlocked the key is
also part of the hibernation image, protected by the disk encryption when the machine is off.
Vault encryption, master password and the data on disk are unchanged. To keep the stronger store
instead, delete the file and quit Bitwarden before each hibernate; with `lid_close = "hibernate"`
the lid then does nothing whenever Bitwarden is open.

Any other app that uses `memfd_secret` blocks hibernate the same way. To find it (the holder is
often not readable without root, as Bitwarden's process wasn't):

```sh
sudo sh -c 'for p in /proc/[0-9]*; do ls -l $p/fd 2>/dev/null | grep -q secretmem && echo "$p $(cat $p/comm)"; done'
```

Source: https://github.com/bitwarden/clients/blob/desktop-v2026.10.4/apps/desktop/desktop_native/secure_memory/src/secure_key/mod.rs

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

Follow-up, 2026-11-24 (KDE session): after a restore EasyEffects had dumped core and the keyboard
backlight stayed dark.

- EasyEffects: `easyeffects.service` was `After=`/`Requisite=graphical-session.target`, which
  makes an ordering cycle with KDE's `plasma-workspace.target` (`Before=graphical-session.target`).
  systemd dropped the job at login and EasyEffects' own XDG autostart copy ran instead
  (`app-com.github.wwmm.easyeffects@autostart.service`), which the hook didn't stop: it aborted with
  "No connection to PipeWire" when PipeWire went down. Fix: no ordering on
  `graphical-session.target` in the unit, and the hook also stops any EasyEffects autostart unit.
- Keyboard backlight: the LED sits on the T2 USB bus, so the driver reload re-creates it. UPower
  kept the old one open (`upowerd: writing '2932' to device failed`). Fix: the hook saves the
  level before the unload, writes it back once the LED is there, and restarts UPower.
- Bluetooth: dead after every real restore since 2026-11-16 (`hci0: Opcode 0x0c24 failed: -16`,
  scans and connects fail although the controller says powered). The BCM4364 hangs off the UART,
  not the T2; the power-off resets the chip under a driver that keeps the old state. Fix: if `hci_uart` is loaded, the
  hook unloads it before the image and loads it again after the restore (`modprobe -r hci_uart && modprobe
  hci_uart` brought it back by hand).

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
