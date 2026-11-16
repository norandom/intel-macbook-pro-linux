# Hibernate (suspend to disk): grow the swap LV

Owner-run, not automated. Swap and LVM are on the protected list
(`.kiro/steering/protected-system-boundary.md`); these steps are a deliberate, manual exception.

## Why it's needed

Hibernate writes the contents of RAM into swap. This machine has 64 GiB of RAM but only 16 GiB of
disk swap (`vg0-swap`). That works only while the RAM in use (minus caches) is below roughly 15 GiB.
With containers, browsers and agents running it fails, and the machine simply stays awake. zram
doesn't help: hibernation can't write to compressed RAM.

Everything else is already in place: hibernation is enabled in the kernel, Secure Boot is off, the
resume device (`/sys/power/resume` = `252:1`, the swap LV) is set, and systemd's hibernate units
exist. So the only change is a bigger swap LV.

## The plan

Layout, checked 2026-11-16: partition `nvme0n1p4` (LUKS, opened as `cryptlvm`) holds volume
group `vg0` with no free space:

| LV | Size | Used |
|---|---|---|
| `vg0-swap` | 16 GiB | swap, UUID `d2e7bb1c-add5-4b87-92ee-6dbb31c9adff` |
| `vg0-root` | 400 GiB | 31 GB |
| `vg0-home` | 696.31 GiB | 5.4 GB |

Target: swap **80 GiB** (64 GiB RAM plus headroom), `/home` shrunk by 64 GiB to **632.31 GiB**.

The swap LV keeps its **path and UUID**. That matters: fstab names it as `/dev/mapper/vg0-swap`,
and there's no `resume=` on the kernel command line. The initramfs found the swap automatically
when it was built and recorded it by UUID, which is how `/sys/power/resume` ends up as `252:1`.
Same UUID, same LV path: fstab, crypttab, the resume device and the initramfs all stay as they
are, and nothing gets regenerated.

## Before you start

1. **Back up `/home`.** Shrinking an ext4 filesystem with these tools is routine, but a backup is
   what makes a typo survivable.
2. Check the numbers on the running system:
   ```sh
   sudo vgs vg0          # VFree should be 0
   sudo lvs vg0          # swap 16g, root 400g, home 696.31g
   df -h /home           # used space must be far below 632 GiB
   sudo blkid /dev/vg0/swap    # note the UUID (d2e7bb1c-... on the owner's machine)
   ```
3. Have a **live USB with T2 support** ready: a t2linux Ubuntu or Kubuntu ISO
   (https://wiki.t2linux.org/), the same kind you installed from. A KDE live session works fine. A stock Ubuntu ISO has no T2 drivers, so the internal keyboard and
   trackpad don't work there; with a stock ISO, bring an external USB keyboard. `/home` can't be
   shrunk while it's mounted, and you can't unmount it while logged in.
4. Have the **LUKS passphrase** at hand.

## On the live USB

Boot the live USB (hold Option at power-on and pick "EFI Boot"; external boot is already allowed if
you installed Linux from USB), choose "Try" / the live session, and open a terminal (Konsole).

**In a KDE live session, ignore the disk pop-ups.** The device notifier offers to unlock and open
the encrypted disk. Don't click it: you unlock in the terminal below, and nothing from `vg0` may be
mounted while you resize. If you already clicked it, step 0 deals with it.

```sh
# 0. Tools present, nothing of vg0 mounted or in use.
command -v lvs cryptsetup mkswap        # lvm2 + cryptsetup; if lvs is missing: sudo apt install lvm2
lsblk -o NAME,SIZE,TYPE,MOUNTPOINTS /dev/nvme0n1
#    If nvme0n1p4 is already open (as luks-<uuid>, because KDE unlocked it), use that name below
#    instead of cryptlvm, and unmount anything of vg0 that shows a mount point:
#    sudo umount /dev/vg0/home /dev/vg0/root 2>/dev/null

# 1. Unlock and activate (skip the cryptsetup line if it's already open).
sudo cryptsetup open /dev/nvme0n1p4 cryptlvm      # asks for the LUKS passphrase
sudo vgchange -ay vg0
sudo lvs vg0                                       # swap 16g, root 400g, home 696.31g
sudo swapoff /dev/vg0/swap 2>/dev/null || true     # in case the live system enabled it
findmnt -S /dev/mapper/vg0-home || echo "home not mounted: good"

# 2. Shrink /home by 64 GiB: lvreduce -r runs e2fsck, then resize2fs, then shrinks the LV.
#    Answer y if it asks to confirm.
sudo lvreduce -r -L -64G vg0/home
sudo vgs vg0                                       # VFree now 64g

# 3. Grow swap into all the freed space and re-create it with the SAME UUID.
uuid=$(sudo blkid -s UUID -o value /dev/vg0/swap); echo "$uuid"   # d2e7bb1c-...
sudo lvextend -l +100%FREE vg0/swap
sudo mkswap -U "$uuid" /dev/vg0/swap
sudo blkid /dev/vg0/swap                           # UUID unchanged
sudo lvs vg0                                       # swap 80g, home 632.31g

# 4. Close everything cleanly, then reboot without the USB stick.
sudo vgchange -an vg0
sudo cryptsetup close cryptlvm                     # or luks-<uuid> if KDE opened it
```

`lvreduce -r` refuses to shrink below the used space and stops on filesystem errors, so it can't
silently cut data off. If it complains, stop and check before trying anything else. If
`vgchange -an` says the volume group is in use, something still has it open (a KDE file manager
window, a mount): close that and run it again.

## Back in Ubuntu

```sh
swapon --show            # /dev/dm-1 now 80G (priority -1), zram0 4G (priority 100)
cat /sys/power/resume    # still 252:1
df -h /home              # ~632G
```

## Switch Hibernate back on

Hibernate was taken out of the power menu while it couldn't work (backlog). The guarded entry is in
git history (`hypr-hibernate`, commit 0bb7ba8): it refuses to hibernate when the RAM in use wouldn't
fit into free disk swap. Ask for it to be restored, or bring it back from that commit, then:

```sh
.venv/bin/pyinfra @local tasks/desktop.py --use-sudo-password
```

## First test

Save your work and close what you can, then:

```sh
systemctl hibernate
```

The machine powers off. On power-on you enter the LUKS passphrase as usual. The kernel then finds
the image in swap and restores your session, and the lock screen follows. Check Wi-Fi, the Touch
Bar and audio afterwards; on T2 Macs those are the usual suspects after any sleep.

## If something goes wrong

- **Normal boot instead of restore** (session lost): check `journalctl -b -1 | grep -i -E 'hibernat|PM: '`.
  Most often the image didn't fit or the resume device didn't match; `cat /sys/power/resume` should
  still be `252:1`.
- **"Not enough suitable swap space"** from systemd: the swap LV isn't active (`swapon --show`) or is
  still 16 GiB.
- **Black screen after restore with backlight**: same fix as for suspend, handled by hypridle's
  delayed `dpms on`; `hyprctl dispatch dpms on` over SSH/Tailscale recovers a running session.

## Going back

To return to the old layout, reverse the steps on the live USB: `swapoff` isn't needed there;
`lvreduce -L 16G vg0/swap`, `mkswap -U "$uuid" /dev/vg0/swap`, then `lvextend -r -l +100%FREE vg0/home`
(online growing of ext4 also works from the running system: `sudo lvextend -r -L +64G vg0/home`
after shrinking swap from the live USB).
