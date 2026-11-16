# Verbose boot and shutdown (owner-run)

Kubuntu hides boot and shutdown behind Plymouth's animation. The kernel command line asks for
that with two words, `quiet splash`, in `/etc/default/grub`. Bootloader configuration is on the
protected list (`.kiro/steering/protected-system-boundary.md`), so this is a manual change, not
part of the deploy.

## What changes

Without `quiet` the kernel prints its messages; without `splash` Plymouth stays out of the way.
You then see the kernel and systemd lines scrolling during boot and during shutdown, which is
also how you spot a service that hangs at shutdown.

The LUKS passphrase prompt changes too: instead of Plymouth's graphical box you get a plain text
prompt (`Please unlock disk cryptlvm:`). It works the same way, keyboard included, because the
T2 keyboard modules are in the initramfs either way. Kernel messages can print over the prompt
line; just keep typing and press Enter.

## Do it

```sh
sudo cp /etc/default/grub /etc/default/grub.before-verbose
sudoedit /etc/default/grub
```

Change

```
GRUB_CMDLINE_LINUX_DEFAULT='quiet splash intel_iommu=on iommu=pt pm_async=off'
```

to

```
GRUB_CMDLINE_LINUX_DEFAULT='intel_iommu=on iommu=pt pm_async=off'
```

Keep the other three options: they're part of the T2 setup (`pm_async=off` keeps suspend working).
Then:

```sh
sudo update-grub
```

Nothing else needs regenerating; the initramfs stays as it is.

## Check

After a reboot, `cat /proc/cmdline` no longer contains `quiet splash`. `systemd-analyze
blame` and `journalctl -b` are still there if you want the details afterwards.

## A middle ground

To keep the animation but see messages when you want them, leave the line alone and press
**Esc** during boot or shutdown: Plymouth switches to the text view for that time.

## Going back

```sh
sudo cp /etc/default/grub.before-verbose /etc/default/grub && sudo update-grub
```
