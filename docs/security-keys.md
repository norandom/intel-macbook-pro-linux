# Security keys instead of Touch ID

Touch ID doesn't work on Linux: the T2 chip keeps the fingerprint sensor to itself. The
replacement here is a YubiKey (any FIDO2/U2F key works). Touch the key instead of typing your
password for sudo, admin prompts, the login screen and the lock screen.

Buy two and register both: a primary on your keyring and a spare in a drawer. If you lose one,
you remove it and carry on with the other. Your password keeps working in every case.

## What the deploy sets up

`tasks/security_keys.py` always installs:

- `ykman` (yubikey-manager) for the key itself: FIDO2 PIN, OATH codes, PIV;
- `pam_u2f` and `pcscd`;
- `t2-yubikey`, a small helper to register keys.

Touching the key for login only happens when you switch it on (`yubikey_login = true`) and at
least one key is registered.

## Set it up

```sh
t2-yubikey register        # primary key: touch it when it blinks
t2-yubikey add-spare       # unplug the primary, plug in the spare, touch it
t2-yubikey status
```

Then set the flag in `~/.config/t2-mac-kde/config.toml` and run the task:

```toml
yubikey_login = true
```

```sh
.venv/bin/pyinfra @local tasks/security_keys.py --use-sudo-password
```

Before you run it, open a second terminal with `sudo -i` and leave it open. If anything about
the login stack goes wrong, that root shell lets you undo it.

Then test, in a new terminal:

```sh
sudo -k; sudo true      # key plugged in: "Please touch the device", touch it
                        # key unplugged: the usual password prompt
```

Lock the screen (SUPER+Escape or wait) and unlock by touching the key; press Enter on the empty
password field first if hyprlock waits for input.

## How it works

The deploy adds a `pam-auth-update` profile (`t2-u2f`), the same mechanism Ubuntu uses for
fingerprint login. pam_u2f sits in front of the password check as an alternative: key touched,
you're in; no key or no touch, the password prompt follows. Only these services ask for the
key: `sudo`, `su`, polkit (admin prompts), SDDM and the console login, and hyprlock. SSH, cron
and everything else stay password-only, so an SSH login never waits for a key that sits in the
laptop.

The registered keys are copied to `/etc/t2-mac-kde/u2f_mappings`, owned by root. A file in your
home directory would let any program running as you add its own key and then sudo without a
password; the root-owned copy prevents that. You register into
`~/.config/t2-mac-kde/u2f_keys`, and the deploy copies it over.

Keys are bound to the origin `pam://t2-mac-kde`, not the hostname, so renaming the machine
doesn't break them.

## Lost a key, or turn it off

- Lost key: delete `~/.config/t2-mac-kde/u2f_keys`, register the remaining key (and a new
  spare) again, run the task.
- Off: `yubikey_login = false`, run the task. It disables the profile and removes it.

The disk unlock at boot (LUKS) is not touched: it stays a passphrase. That part of the boot is
off limits for this repository ([safety.md](safety.md)).
