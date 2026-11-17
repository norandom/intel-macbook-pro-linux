# Commands

These land in `~/.local/bin` or your shell. Most of the desktop ones are also on a key or a bar
button, so the command line is just the second way in.

## Power and battery

| Command | What it does |
|---|---|
| `turbo-on` / `turbo-off` / `turbo-status` | Intel turbo boost on or off (off after every boot) |
| `hypr-power-profile balanced` | power-saver, balanced or performance; the battery icon has the same menu |
| `hypr-brightness screen -5` | screen or keyboard light (`kbd`); one step below the minimum turns the panel off |
| `t2-battery status` / `full` / `limit` | charge limit (config `battery_charge_limit`, e.g. 80 %); `full` before a trip |
| `hypr-gpu battery` / `external` / `status` | Hyprland on the Intel GPU only, or with the AMD-driven external ports; applies at the next login (`--now` logs out) |

## Audio

| Command | What it does |
|---|---|
| `hypr-3d stage` | headphone preset: `plain`, `room`, `stage`, `plus` or `auditorium` |
| `hypr-3d off` / `hypr-3d on` | headphone effects off for a straight A/B comparison, and back on |
| `hypr-volume up` / `down` / `mute` / `micmute` | volume and mic keys with the on-screen popup |

## Desktop (Hyprland)

| Command | What it does |
|---|---|
| `hypr-screenshot edit` | rectangle to `~/Screenshots`, then the Satty editor (SUPER+SHIFT+4) |
| `hypr-touchpad speed +0.1` / `scroll 0.8` / `tapdrag on\|off` / `reset` | trackpad feel, remembered |
| `t2-yubikey register` / `add-spare` / `status` | YubiKeys for sudo and login ([security-keys.md](security-keys.md)) |
| `hypr-layout next` | dynamic (floating, the default) or golden-ratio tiling (SUPER+L) |
| `hypr-nightmode next` | screen filter: off, green, dark, grayscale, monochrome or warmwhite (the rabbit in the bar) |
| `hypr-nightshift toggle` | pause or resume the night shift (the moon in the bar) |
| `hypr-deco win311` / `mac` | title bar style; `hypr-shadow on` / `off` for shadows |
| `hypr-kbd de` / `us` | keyboard layout (aliases `kbde`, `kbus`) |
| `hypr-findcursor` | flashes a huge pointer so you can find it (SUPER+SHIFT+C) |

## Terminal and themes

| Command | What it does |
|---|---|
| `hypr-termtheme next` | next of the five terminal/editor themes (SUPER+Y); or name one, e.g. `navy` |
| `k` | `kubectl` with completion |
| `dl` | `aria2c` with parallel connections |

## System

| Command | What it does |
|---|---|
| `t2-alerts` / `t2-alerts ack` / `t2-alerts log` | storage and service alerts, acknowledge them, NVMe health history |
| `hypr-rdp-control status` | the RDP server inside the Hyprland session (`start`, `stop`, `validate`) |
| `dev-disk-reclaim` | shows what caches and builds could be cleaned; `--apply` cleans them |

## Nix tools ([nix.md](nix.md))

| Command | What it does |
|---|---|
| `t2-nix-update` | updates every Nix tool at once, copies the new `flake.lock` to the repo to commit |
| `nix profile list` | what the profile holds (one entry, `t2-tools`) |
| `nix profile rollback` | back to the previous tool set |

## Full local deployment

Run `./deploy.sh` as the desktop user (without sudo). It invokes the repository's
`.venv/bin/pyinfra @local deploy.py --use-sudo-password` and forwards extra arguments.
Use `./deploy.sh --dry` to preview; privileged fact collection may still require sudo authentication.

The resource policy configures open-file limits of 65,536 soft / 1,048,576 hard
for PAM logins and systemd system/user managers. Reboot after deployment to apply
them throughout the session; existing processes retain their inherited limits.
Individual service overrides can still set different limits.
