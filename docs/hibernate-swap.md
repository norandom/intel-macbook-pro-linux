# Hibernate: grow the swap LV (owner-run, not automated)

Swap/LVM are on the protected list (`.kiro/steering/protected-system-boundary.md`).
These steps are an owner-authorized, manual exception. They keep the swap LV's
**path and UUID**, so fstab (`/dev/mapper/vg0-swap`), crypttab, the resume device and
the initramfs need no change and nothing is regenerated.

Layout (2026-11-15): LUKS `cryptlvm` 1112.31 GiB = `vg0` with no free extents:
swap 16 GiB, root 400 GiB (9.5 GB used), home 696.31 GiB (4.6 GB used). RAM 64 GiB.
Target: swap 80 GiB (64 GiB RAM + headroom), home shrunk by 64 GiB to 632.31 GiB.

**Back up /home first.** Shrinking a filesystem is safe with these tools, but only a
backup makes it safe against mistakes.

## Do it from a live USB (Ubuntu 26.04 ISO): /home must not be mounted

```sh
sudo cryptsetup open /dev/nvme0n1p4 cryptlvm      # your LUKS passphrase
sudo vgchange -ay vg0
sudo lvs vg0                                       # expect swap 16g, root 400g, home 696.31g

# 1. shrink home: fsck + resize2fs, then the LV (lvreduce -r does both, in that order)
sudo lvreduce -r -L 632.31G vg0/home

# 2. grow swap and re-create it with the SAME UUID (and no label change)
uuid=$(sudo blkid -s UUID -o value /dev/vg0/swap); echo "$uuid"   # d2e7bb1c-...
sudo lvextend -L 80G vg0/swap
sudo mkswap -U "$uuid" /dev/vg0/swap
sudo blkid /dev/vg0/swap                            # same UUID as before

sudo vgchange -an vg0 && sudo cryptsetup close cryptlvm
```

Reboot into Ubuntu, then check: `swapon --show` (dm-1 now 80G), `cat /sys/power/resume`
(still 252:1), `df -h /home`.

## Use it

- Power menu (bar power button or SUPER+ESCAPE): **Hibernate**. `hypr-hibernate` refuses
  (with a notification) when used RAM would not fit the free disk swap.
- Resume asks for the LUKS passphrase (the image is inside the encrypted volume), then
  restores the session; the lock screen follows.
- T2: test once with nothing important open; check Wi-Fi, Touch Bar, audio after resume.
