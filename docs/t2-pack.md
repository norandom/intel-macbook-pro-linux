# The T2 pack: tested versions, pinned and released

This repository is tested against one exact set of versions for the parts that break when they
change: the T2 kernel, the T2 support packages, and Hyprland. That set is the T2 pack, written
down in [`t2-pack.toml`](../t2-pack.toml). Releases are tagged against it. When the T2 repo or
Ubuntu ships something newer, the machine stays on the pack until the new versions have been
ported and tested; then the manifest moves and a new release follows.

Current pack: `t2-7.3.4-3`

| Package | Version | Why it's in the pack |
|---|---|---|
| `linux-t2` + image + headers | 7.3.4-3 | T2 drivers (`t2bce_*`), hibernate hook, suspend, benchmarks |
| `apple-t2-audio-config` | 0.5.3-resolute | speaker and mic profiles the audio DSP builds on |
| `apple-firmware-script` | 1.4-3 | Wi-Fi and Bluetooth firmware |
| `hyprland`, `hyprland-dev` | 0.53.3+ds-4 | the patched hyprbars build is tied to it |
| `hyprland-plugin-hyprbars` | 0.53.0-1 | fallback title bars if our build is missing |

## The pin

With `t2_pack_pin = true` in `~/.config/t2-mac-kde/config.toml`, `tasks/t2_pack.py` writes
`/etc/apt/preferences.d/90-t2-pack.pref`. It gives the pack's versions priority 990, so
`apt upgrade` leaves these packages alone and everything else updates as usual. It never forces
a downgrade (that would need a priority above 1000). The deploy itself installs, upgrades and
removes nothing. It's an opt-in exception to the protected boundary
(`.kiro/steering/protected-system-boundary.md`); `false` removes the file again.

```sh
.venv/bin/pyinfra @local tasks/t2_pack.py --use-sudo-password
```

Security fixes for these packages wait for the next pack too. That's the trade: a kernel or
Hyprland update can't break hibernate, audio or the title bars behind your back, but you have
to port to get them.

## No background updates

With `background_updates = false`, the same task stops everything apt does on its own: the
twice-daily package-list refresh (`apt-daily`), unattended security upgrades
(`apt-daily-upgrade`, `unattended-upgrades`) and Ubuntu's update notifier. It writes
`/etc/apt/apt.conf.d/99-t2-no-background-updates` and disables those units. Nothing locks apt
behind your back any more, and nothing changes the system while you work. The price: security
updates arrive only when you run them.

```sh
sudo apt update && sudo apt upgrade     # weekly, or when a security notice matters
```

`true` (Ubuntu's default) removes the file and turns exactly those units back on.

## The .deb backup

The same task (config `t2_pack_backup`, on by default) downloads the pack's packages to
`~/.local/share/t2-mac-kde/t2-packs/<pack id>/`, about 150 MB, mostly the kernel. apt checks
them against the signed repo index while downloading, and the tool checks them again against
[`packs/<pack id>.sha256`](../packs/), committed with the pack. If the T2 repo or Ubuntu ever
drops these versions, you can still install them:

```sh
cd ~/.local/share/t2-mac-kde/t2-packs/t2-7.3.4-3 && sha256sum -c SHA256SUMS
sudo apt install ./linux-t2_*.deb ./linux-image-*.deb ./linux-headers-*.deb   # example: the kernel
```

## Checking for a new pack

```sh
tools/t2-pack check
```

shows the pack, what's installed, and any newer version in the configured repos. Exit code 1
means the installed versions differ from the pack.

## Porting to a new pack

1. On a branch, run `tools/t2-pack check` to see what's new.
2. Bump `t2-pack.toml`: the new versions, a new `id` (named after the T2 kernel, e.g.
   `t2-7.3.5-1`), and `tested` once you're done.
3. Run `tasks/t2_pack.py` so the pin points at the new versions, then upgrade them yourself:
   `sudo apt install linux-t2 hyprland hyprland-dev ...`, and reboot.
4. Port what broke. Usual suspects: the hyprbars patch (`files/desktop/hyprbars/`, rebuilt by
   the desktop deploy), the hibernate hook (`t2bce_*` module names), the speaker DSP.
5. Test on the machine: `docs/t2-tests/` (suspend, hibernate round-trip, driver reload), audio,
   touch bar, keyboard and trackpad after resume, title bars. Optionally the benchmark.
6. `tools/t2-pack backup --record` downloads the new .debs and writes `packs/<id>.sha256`.
   Commit, merge.

## Releasing

```sh
tools/t2-pack release            # checks, then tags <date>-<pack id>, e.g. 2026.11.16-t2-7.3.4-3
tools/t2-pack release --push     # also pushes the tag and creates the GitHub release
tools/t2-pack release --push --debs   # ... and attaches the .debs to the release
```

It refuses to tag when the installed versions differ from the pack, when the working tree isn't
clean, or when the backup doesn't match `packs/<id>.sha256`. The release notes list the pack.

A note on `--debs`: the kernel is GPL. Attaching its binary to a public release means the
matching source must stay available; it is, in the
[t2linux](https://github.com/t2linux/T2-Debian-and-Ubuntu-Kernel) and
[t2-ubuntu-repo](https://github.com/AdityaGarg8/t2-ubuntu-repo) repositories. Without `--debs`
the copies stay on this machine only.
