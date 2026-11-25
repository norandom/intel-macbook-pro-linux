# Configuration

Your settings live in `~/.config/t2-mac-kde/config.toml`, never in the repository. The deploy
keeps a fully commented `config.example.toml` next to it (source: `files/config.example.toml`).
Every key is optional. The order of precedence is:

1. `--data key=value` on the pyinfra command line;
2. `config.toml`;
3. the task's default.

```sh
mkdir -p ~/.config/t2-mac-kde
cp files/config.example.toml ~/.config/t2-mac-kde/config.toml   # then uncomment what you need
```

## Running the deploy, or one task

```sh
.venv/bin/pyinfra @local deploy.py --dry --use-sudo-password   # preview everything
.venv/bin/pyinfra @local deploy.py --use-sudo-password         # apply everything

.venv/bin/pyinfra @local tasks/desktop.py --dry                # preview one task
.venv/bin/pyinfra @local tasks/desktop.py --use-sudo-password  # apply one task
.venv/bin/pyinfra @local tasks/rdp.py --data rdp_fps=30        # one-off override
```

Run it as your normal user; only the system parts ask for the sudo password. After changing a
config key, re-run the task that reads it (listed below). The tasks are idempotent, so a re-run
only changes what differs.

Tasks with an order: `shell` needs `node` and `tools` first; `themes` should run after
`vendor_apps`, because it only themes editors that are already installed. `deploy.py` lists them
in a working order.

To leave a task out for good, see [forking.md](forking.md#disabling-a-whole-task).

## Desktop

Read by `tasks/desktop.py` (fonts: `tasks/fonts.py`).

| Key | Default | Effect |
|---|---|---|
| `panel_scale` | `"auto"` | Internal panel (eDP-1) scale, e.g. `1.6` on the 16" Retina panel |
| `desktop_left_reserve` | `0` | Pixel strip at the panel's left edge kept free of windows |
| `cursor_theme` | `"breeze_cursors"` | `"t2-highvis"` = large white arrow with a red outline |
| `cursor_size` | `24` | e.g. `48` for a much bigger pointer |
| `password_store` | `"kwallet6"` with KDE, else `"gnome-libsecret"` | Password backend for Chromium and Electron apps; `""` = don't set one |
| `browser_video` | `true` | Vivaldi/Chromium: VA-API video decoding on the Intel GPU, YouTube kept off AV1 (enhanced-h264ify) |
| `reserved_cores` | `1` | Cores (both threads) kept free of terminal jobs and Docker containers; `0` = off |
| `build_jobs` | `0` | Job count for GOMAXPROCS, cargo, nextest, pytest-xdist, CMake/CTest; `0` = the allowed threads |
| `gpu_mode` | `"battery"` | First-run GPU mode; afterwards `hypr-gpu` decides |
| `bar_graphs` | `false` | CPU, memory and network as sparklines instead of numbers |
| `decorations_style` | `"win311"` | Initial title bar style (`"win311"` or `"mac"`); afterwards `hypr-deco` |
| `window_shadows` | `"off"` | Initial shadows (`"off"`, `"mac"`, `"win311"`); afterwards `hypr-shadow` |
| `fleet_hosts` | `[]` | Hostnames that should get clearly distinct title bar colours |
| `[decor_colors]` | empty | Per-host colour override, `hostname = "#rrggbb"` |
| `[default_apps]` | empty | MIME type = desktop file, applied with `xdg-mime` |
| `[[mounts]]` | none | Network folders mounted at login in KDE and Hyprland (rclone or sshfs); see below |
| `font_rendering` | `"grayscale"` | `"rgb"` for subpixel rendering (fontconfig) |
| `night_shift` | `false` | `true`: warmer screen after sunset, like f.lux (gammastep; [desktop.md](desktop.md)) |
| `night_shift_location` | `""` | `"lat:lon"`; empty = the city of the system timezone |
| `night_shift_day` / `night_shift_night` | `6500` / `4500` | Colour temperature in K by day and at night |

`font_rendering` is also used for the first GTK `settings.ini`, which the desktop task only
writes if the file doesn't exist; there its default is `"rgb"`.

## Power and privacy

Read by `tasks/resource_policy.py` (mitigations: `tasks/cpu_mitigations.py`).

| Key | Default | Effect |
|---|---|---|
| `fan_curve` | `true` | Earlier cooling (`tasks/fan_curve.py`): full fans by 85°C; false restores SMC policy |
| `battery_charge_limit` | `100` | Stop charging at this percentage (50 to 100; 100 = no limit) |
| `power_tuning` | `false` | Runtime PM for three Intel chipset functions, fewer wakeups |
| `crash_upload` | `true` | `false` masks whoopsie: no uploads to errors.ubuntu.com |
| `cpu_mitigations_off` | `false` | `true` adds `mitigations=off` at the next reboot ([cpu-mitigations.md](cpu-mitigations.md)) |
| `t2_pack_pin` | `false` | `true` holds the T2 kernel and Hyprland at the versions in `t2-pack.toml` ([t2-pack.md](t2-pack.md)) |
| `background_updates` | `true` | `false` stops apt-daily, unattended-upgrades and the update notifier ([t2-pack.md](t2-pack.md)) |
| `t2_pack_backup` | `true` | Keep `.deb` copies of the pack in `~/.local/share/t2-mac-kde/t2-packs/` |

## Network

Read by `tasks/network_tuning.py` and `tasks/traffic_shaping.py`
([remote-access.md](remote-access.md#tcp-tuning)).

| Key | Default | Effect |
|---|---|---|
| `network_tuning` | `true` | BBR congestion control, no slow start after idle, MTU probing; `false` restores the kernel defaults |
| `cake_upload_mbit` | `0` | CAKE shaper for uploads, in Mbit/s; set about 90-95 % of the measured speed; `0` = off |
| `cake_download_mbit` | `0` | The same for downloads |

## Shell and developer tools

Read by `tasks/shell.py`.

| Key | Default | Effect |
|---|---|---|
| `shell_blesh` | `false` | ble.sh suggestions, syntax colours and completion menu in Bash |
| `shell_prompt` | `"builtin"` | `"starship"`: Starship prompt in bash and fish (language symbols, palette colours) |
| `shell_interactive` | `"bash"` | `"fish"`: every terminal hands over to fish (grml aliases, functions and prompt ported; bash stays the login shell) |
| `safe_chain` | `false` | Aikido Safe Chain in front of npm, pip, uv and friends |
| `rclone_mounts` | `{}` | `{ remote = "Dir" }`: mount each rclone remote at `~/Dir` |
| `rclone_cache_size` | `"10G"` | VFS cache size per mount |
| `rclone_cache_age` | `"24h"` | How long cached files are kept |

## Nix

Read by `tasks/nix_tools.py` (and `tasks/apps.py`, `tasks/containers.py` to avoid installing a
tool twice). See [nix.md](nix.md).

| Key | Default | Effect |
|---|---|---|
| `nix_tools_extra` | `[]` | nixpkgs attributes added on top of the default set |
| `nix_tools` | the list in `manage/nix_tools.py` | Replaces the default set. `[]` keeps only apt and release tools; leaving out zellij, kubectl, helm, k9s, ktop, bitwarden-cli, rclone or podman-tui brings back their pinned release binary |

## Themes

Read by `tasks/themes.py`.

| Key | Default | Effect |
|---|---|---|
| `themes_chromium_policy` | `false` | Write the Chromium theme policy (needs `/etc/chromium`) |

## Audio

Read by `tasks/audio_effects.py` and `tasks/speaker_dsp.py`.

| Key | Default | Effect |
|---|---|---|
| `music_headphones` | every paired Bose device | Bluetooth names or MACs that get the 3D preset and music-only mode |
| `music_preset` | `"plain"` | `"plain"`, `"room"`, `"stage"`, `"room+"`, `"auditorium"` |
| `music_codec` | `"sbc"` | `"sbc_xq"` is cleaner but may tick with Wi-Fi on 2.4 GHz |
| `music_boost_db` | `0` | Extra level for the music headphones |
| `speaker_dsp` | `false` | Speaker DSP on the MacBookPro16,1; `false` and a re-run removes it |

The older key `qc35_mac` still works as a fallback for `music_headphones`.

## RDP

Read by `tasks/rdp.py`.

| Key | Default | Effect |
|---|---|---|
| `rdp_bind` | `"0.0.0.0:3389"` | Listen address; the firewall only lets Tailscale and loopback in |
| `rdp_egfx_codec` | `"clearcodec"` | `"avc420"` for H.264 |
| `rdp_fps` | `20` | Frame rate |
| `rdp_audio_mode` | `"mirror"` | `"mirror"` or `"off"` |

## Remote access

| Key | Default | Effect |
|---|---|---|
| `hibernate` | `false` | `true`: Hibernate in the power and Apps menus, allowed by a polkit rule (Ubuntu forbids it by default); needs disk swap at least as big as RAM ([hibernate-swap.md](hibernate-swap.md)). Uses `HibernateMode=shutdown`, because Apple's firmware hangs in the ACPI S4 call ([known-issues.md](known-issues.md)) |
| `lid_close` | `"suspend"` | `"hibernate"`: closing the lid hibernates, on battery and on power; only together with `hibernate = true`. With an external monitor attached the lid is ignored, as before |
| `yubikey_login` | `false` | `true`: touch a registered YubiKey instead of the password for sudo, polkit, login, lock screen ([security-keys.md](security-keys.md)) |

## Example

Mine looks roughly like this:

```toml
panel_scale = 1.6              # internal panel scale
desktop_left_reserve = 15      # my panel has dead pixel columns at the left edge
music_headphones = ["My QC35"] # Bluetooth name or MAC: these get the 3D preset
music_preset = "stage"
speaker_dsp = true
shell_blesh = true
crash_upload = false
```

Tables such as `[default_apps]` go after the plain keys, because everything below a table header
belongs to that table.

## Network folders (`[[mounts]]`)

Each `[[mounts]]` entry becomes the user service `t2-mount@<name>`, started at login in KDE and
Hyprland (`tasks/mounts.py`). At login without a network it waits in the background.

```toml
[[mounts]]
name = "onedrive"        # t2-mount@onedrive
type = "rclone"          # cloud remote with a local cache (50G, offline use of cached files)
source = "OneDrive:"     # a remote from ~/.config/rclone/rclone.conf
path = "~/OneDrive"
options = ["--onedrive-delta"]      # extra rclone flags; they override the defaults
offline = ["Configs", "Obsidian"]   # folders kept fully in the cache

[[mounts]]
name = "filer"
type = "sshfs"           # SFTP share, no local cache: media players can seek freely
source = "filer:/share"  # [user@]host:path; a Host from ~/.ssh/config works
path = "~/Filer"
```

Logins are not part of the config: rclone remotes come from `rclone config`, sshfs needs an SSH
key login (`ssh-copy-id`), because it never asks for a password. Commands:
`systemctl --user status 't2-mount@*'`, `systemctl --user restart t2-mount@filer`. Logs:
`~/.cache/rclone/<remote>-mount.log` and `~/.cache/t2-mount/<name>-sshfs.log`. Removing an
entry disables its service at the next deploy; the folder stays mounted until logout.
For video from an sshfs share, use Haruna or mpv: VLC's MKV reader needs a minute there.

## Ubuntu reporting

Resource policy defaults crash_upload to false (whoopsie stopped/masked), disables
GNOME technical reports and software-usage statistics, disables/masks MOTD news
fetches, opts out of popularity-contest when installed and disables ubuntu-report's
user autostart. Existing explicit crash_upload=true overrides the default; set it
false for this policy. Local apport diagnostics remain available. Ubuntu Pro,
security updates and ordinary package-repository traffic are not disabled by these
reporting controls. No live reporting-setting changes are made by a dry run.

### Earlier cooling

The default `t2-fan-curve.service` monitors the hottest Intel CPU or AMD GPU
edge/junction sensor every second. It leaves firmware cooling in charge below 70°C,
then requests stepped speeds: 40% at 70°C, 55% at 75°C, 75% at 80°C and 100%
at 85°C. There is no interpolation. Cooling down requires 2°C below a step's
threshold before dropping a level; at 65°C it returns to automatic SMC control.
Each fan respects its hardware minimum and the firmware target observed on takeover.
90°C is a cooling target, not a guaranteed ceiling; CPU power settings are unchanged.

The helper temporarily enables the existing `macsmc_hwmon` runtime `fan_control`
parameter. This is the kernel’s explicitly manual/unsafe interface, so recovery
is essential: sensor errors stop the controller, a 10-second systemd watchdog
handles hangs, and `ExecStopPost` returns every fan to automatic mode before
restoring the parameter. No module is reloaded and no boot configuration is changed.
An existing manual controller is refused. Set `fan_curve = false` and deploy to
stop this service and restore firmware cooling.

Deploy: `.venv/bin/pyinfra @local tasks/fan_curve.py --use-sudo-password`.
Check with `systemctl status t2-fan-curve.service` and `sensors`.
Live fan response and suspend/resume need owner validation after deployment.

The battery’s 80% charge limit is an upper limit, not a continuously maintained
setpoint. The macsmc charging logic uses a five-percentage-point restart gap,
so resting around 75–80% while plugged in is expected. Use `t2-battery status`
to check the configured/current limit and charging state.
