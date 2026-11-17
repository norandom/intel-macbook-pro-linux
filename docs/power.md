# Power, battery and heat

Most of this comes from `tasks/resource_policy.py`; the GPU modes from `tasks/desktop.py`.

## Turbo boost

Turbo is off after every boot (`/etc/tmpfiles.d/no-turbo.conf` writes `no_turbo=1`). The i9
runs cooler, quieter and longer on battery that way, and most desktop work doesn't need it.

```sh
turbo-on       # until the next boot (asks for sudo)
turbo-off
turbo-status   # 1 = turbo off, 0 = on
```

The aliases live in `~/.config/t2-mac-kde/turbo.bash`, sourced by interactive Bash.

## Power profiles

Click the battery or the power profile icon in Waybar to pick power-saver, balanced or
performance (power-profiles-daemon). From a shell: `hypr-power-profile balanced`.

## Battery charge limit

The Apple SMC can stop charging at a limit, which helps a battery that is plugged in most of the
time. Set it in the config:

```toml
battery_charge_limit = 80   # 50..100, 100 = no limit (default)
```

A udev rule applies it whenever the battery shows up. `t2-battery` handles the rest:

```sh
t2-battery status   # limit, state, watts, capacity vs design, cycles, health
t2-battery full     # charge to 100 % until the next reboot or `limit`, e.g. before a trip
t2-battery limit    # back to the configured limit (or `limit 60`)
```

## GPU modes

The Intel iGPU drives the built-in display. The AMD GPU can't be powered off on this Mac, but it
can be left idle. It has to stay available because the external display ports are wired to it.

| Mode | Hyprland renders on | External displays |
|---|---|---|
| `battery` (default) | Intel only | off |
| `external` | Intel, AMD drives the ports | on |

In battery mode nothing renders on the AMD GPU. On my machine it idles at about 3 W that way,
instead of the 8 W it drew back when apps rendered on it.

```sh
hypr-gpu external         # before you plug in a monitor; applies at the next login
hypr-gpu external --now   # same, and log out right away
hypr-gpu battery          # back
hypr-gpu status           # configured vs running mode, AMD load and watts
```

`gpu_mode` in the config only sets the mode on the first run; after that `hypr-gpu` decides.
KDE isn't affected by either mode.

## Memory pressure

- zram swap (lz4, half the RAM, capped at 4 GiB) sits in front of the disk swap with a higher
  priority. Disk swap and resume are untouched.
- earlyoom kills the biggest process when free RAM drops below 5 % and free swap below 10 %.
  The KDE and Hyprland session processes, PipeWire and sshd are deprioritized.
- journald and systemd-coredump are capped at 500 MB each.

## Power tuning (optional)

```toml
power_tuning = true
```

This turns on runtime power management for three Intel chipset functions and sets two kernel
options that cut wakeups (`nmi_watchdog` off, writeback every 15 s). The T2 bridge, the Apple SSD
controller, Wi-Fi, the SMC's LPC bridge and PCIe ASPM are left alone on purpose. Setting it back
to `false` removes the files; the sysctls go back to normal at the next reboot.

`powertop` is installed either way. `sudo powertop` shows where the watts go on battery. Don't run
`powertop --auto-tune`: it also switches the T2 devices, which is what the selective tuning
avoids.

## Fans

The default `fan_curve = true` enables the runtime SMC fan controller. It requests
35% of each fan's maximum at 55°C, 45% at 65°C, 65% at 75°C and full speed at
85°C, interpolating between points and respecting each fan's minimum RPM.
It uses the hottest CPU/GPU sensor and returns to firmware control at 50°C.
The moderate-temperature speeds are relaxed for quieter everyday use; 90°C is a
cooling target, not a guaranteed temperature cap. Set `fan_curve = false` to
restore firmware cooling. Deployment restarts the service when the curve changes.

## Other services

Avahi (mDNS discovery) is masked; printing by IP or hostname still works. With
`crash_upload = false`, whoopsie is masked and nothing goes to errors.ubuntu.com; local crash
capture stays.

## Change it

| You want | Change |
|---|---|
| Turbo on at boot | drop the no-turbo block from `tasks/resource_policy.py`, then `sudo rm /etc/tmpfiles.d/no-turbo.conf` |
| Different zram size | `files/resource-policy/zram-generator.conf` |
| Different earlyoom thresholds or avoid list | `manage/resource_policy.py` |
| Charge limit, power tuning, crash upload | config keys, see [configuration.md](configuration.md#power-and-privacy) |

Re-run: `.venv/bin/pyinfra @local tasks/resource_policy.py --use-sudo-password`.
