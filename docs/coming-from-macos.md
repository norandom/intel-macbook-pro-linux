# Coming from macOS

What you used on the Mac, and what this repository gives you instead. Only things it actually
installs or configures are listed. Where there's no counterpart, the table says so.

## Apps and habits

| On macOS you used | Here it is |
|---|---|
| iStat Menus | The Waybar modules: CPU, memory, temperature (CPU package on the bar; hottest core, both fan speeds, AMD GPU and SSD in the tooltip), network up/down, battery with watts and time left, brightness, power profile. `bar_graphs = true` turns CPU, memory and network into sparklines. Click CPU or temperature for btop. Fans are read-only: the SMC controls them |
| Activity Monitor | btop, htop (sorted by memory), atop |
| Battery health in System Information | `t2-battery status`: capacity vs design, cycles, health |
| AlDente, optimized charging | `battery_charge_limit = 80` and `t2-battery full` before a trip ([power.md](power.md#battery-charge-limit)) |
| Low Power Mode | The power-saver profile (battery icon). Turbo is off by default anyway |
| AirPods battery and noise control | [LibrePods](https://github.com/kavishdevar/librepods), a tray app; not installed by the repo yet ([audio.md](audio.md#airpods-extras)) |
| Magic Keyboard | Works out of the box (kernel driver `hid_apple`, battery reported by the kernel). Not set up yet, but possible later: a Hyprland mapping for that keyboard only (e.g. swap Option and Command) and its battery in Waybar, without touching the built-in keyboard or the boot |
| Trackpad settings | `hypr-touchpad speed +0.1` / `scroll 0.8` / `reset`, remembered ([desktop.md](desktop.md#trackpad)) |
| Boom3D | EasyEffects presets `plain`, `room`, `stage`, `room+`, `auditorium` for your music headphones; `hypr-3d` switches them live. Hyprland session only ([audio.md](audio.md)) |
| The speaker processing macOS does for you | The speaker DSP (`speaker_dsp = true`), MacBookPro16,1 only |
| Microsoft Word | WordCraft, or LibreOffice Writer with the tabbed (ribbon-style) UI |
| Microsoft Excel | GridCraft, or LibreOffice Calc. Real Excel macros: Windows in a VM |
| Microsoft PowerPoint | DeckCraft. LibreOffice Impress isn't installed |
| Adobe Lightroom | LightCraft |
| Adobe InDesign | DesignCraft |
| Adobe Acrobat | PdfCraft; qpdfview and xpdf for viewing |
| Adobe Photoshop | PhotoCraft (Craft suite photo editor) |
| Adobe Illustrator | Not in the Craft suite; Inkscape is the usual Linux choice ([apps.md](apps.md#add-or-remove-an-app)) |
| Adobe Premiere, After Effects | No counterpart installed, and no video player either |
| AutoCAD | CADCraft |
| Preview | qpdfview, xpdf for PDFs; Ristretto for images |
| OneDrive client | An rclone mount at `~/OneDrive` (see below), plus Rclone UI |
| Google Drive for desktop | An rclone mount, e.g. at `~/GoogleDrive` (see below) |
| Spotlight | fuzzel (SUPER+Space) for apps. It searches apps, not file contents |
| Launchpad, the Apple menu | The Apps menu (SUPER+A or the bar's Apps button) |
| Finder | Xfe (SUPER+E or the bar button) |
| Terminal, iTerm2 | Terminator (SUPER+Return), Ghostty, foot, xfce4-terminal, all sharing five themes (SUPER+Y) |
| Cmd+Shift+4 | SUPER+SHIFT+4: rectangle to `~/Screenshots`, then the Satty editor |
| Night Shift | `hypr-nightmode`, the rabbit in the bar |
| Rectangle, Magnet | Windows float by default with gentle snapping; golden-ratio tiling on demand (SUPER+L, SUPER+T per window) |
| A clipboard manager | Clipboard history on SUPER+V, kept in RAM and wiped every night at 01:00 |
| Keychain | KDE Wallet for Chromium and Electron apps in both sessions; Bitwarden |
| Safari | Vivaldi (default), Chromium, Firefox Developer Edition, Zen |
| Notes, Bear | Obsidian, Typora |
| Homebrew | A pinned Nix profile for CLI tools (`nix_tools_extra`, [nix.md](nix.md)), apt for the rest |
| Docker Desktop | Rootless Podman with `docker` and `docker compose`, and Podman Desktop |
| Parallels, VMware Fusion, UTM | virt-manager on KVM, with UEFI and a virtual TPM for Windows 11 |
| Screen Sharing | RDP into the Hyprland session over Tailscale ([remote-access.md](remote-access.md)) |
| Microsoft Remote Desktop | Remote Desktop Manager |
| Remote Login (SSH) | sshd at boot behind fail2ban |
| Xcode | [xtool](https://github.com/xtool-org/xtool): build and deploy iOS apps with SwiftPM, `xtool setup` once ([developer-tools.md](developer-tools.md#ios-apps-with-xtool)) |
| Xcode command line tools | GCC and make; optionally Intel's icx/icpx as your default compiler |
| Time Machine | Coming next: the owner's backup tool will be added. Until then rsync and rclone are installed |
| Touch ID | A YubiKey, primary + spare: touch it for sudo, admin prompts, login and the lock screen ([security-keys.md](security-keys.md)) |

KDE Plasma is still there, with its own apps (Dolphin, System Settings and so on). The table
above is about what this repository adds.

## OneDrive and Google Drive

There's no sync client. Each cloud drive is an rclone mount, run as a user systemd service after
you log in, never through `fstab`. Files are fetched when you open them and kept in a local cache
(10 GB, 24 hours by default). Writes land in the cache and upload in the background, so an edit
survives a dropped connection. When you're offline, only cached files open; the mount retries
until the network is back.

rclone comes from the Nix tool set by default (`rclone version` to check).

**1. Create the remote.** Pick a short name; you'll use it in the config.

```sh
rclone config
# n (new remote), name: onedrive, storage: onedrive
# answer the questions; a browser window opens to log in to Microsoft
```

For Google Drive, the same with name `gdrive` and storage `drive`. Rclone UI can do this step in a
window instead. `rclone listremotes` shows what you have.

**2. Add the mounts to your config** (`~/.config/t2-mac-kde/config.toml`). The left side is the
remote name from step 1, the right side a folder name in your home directory:

```toml
rclone_mounts = { onedrive = "OneDrive", gdrive = "GoogleDrive" }
# optional:
# rclone_cache_size = "20G"
# rclone_cache_age = "48h"
```

Remote names may only use letters, digits, `_` and `-`. Folder names must be plain names (no
`/`) and unique.

**3. Re-run the shell task:**

```sh
.venv/bin/pyinfra @local tasks/shell.py --use-sudo-password
```

It writes `~/.config/systemd/user/rclone-<remote>.service` for each entry and starts it.

**4. Check:**

```sh
systemctl --user status rclone-onedrive.service
ls ~/OneDrive
```

A unit whose remote doesn't exist yet is skipped, not failed. If you create the remote after
step 3, start it with `systemctl --user restart rclone-onedrive.service`. Take an entry out of
`rclone_mounts` and re-run the task to stop and delete its unit; the remote and its cache stay.

The mount uses FUSE (`fusermount3`, from Ubuntu's `fuse3` package). The deploy doesn't request
it by name; it comes in as a dependency of `xdg-desktop-portal`.
