# Intel MacBook Pro on Linux

Apple is winding down macOS support for Intel Macs. I didn't want to retire a perfectly good
MacBook Pro over that, so this repository turns an Intel/T2 MacBook Pro into an Ubuntu 26.04
LTS workstation. Ubuntu supports 26.04 until 2031. The whole setup is one pyinfra deploy you
can read before you run it, and every personal choice can be switched back off.

I use it daily on a MacBook Pro 16" 2019 (MacBookPro16,1). Other T2 models should mostly work,
but I haven't tested them.

## Why bother

Ubuntu 26.04 LTS gets security updates until 2031, which is well past the point where Intel
Macs stop getting macOS updates.

People who have switched report that Linux runs 20–30% faster than macOS on the same Intel
hardware. I haven't benchmarked that myself, so treat it as a claim and measure it on your own
workload.

On my machine the hardware works: speakers, microphone, Wi-Fi, Bluetooth, keyboard, trackpad,
Touch Bar, camera and suspend. Touch ID is the one thing that doesn't. It lives inside Apple's
Secure Enclave, and Linux has no driver for it, so you type your password.

The six built-in speakers get a proper crossover and bass processing, similar to what macOS
does behind the scenes. Without it they sound thin on Linux. Headphones get a 3D preset in the
spirit of Boom3D.

## Two desktops, one machine

You pick a desktop at the login screen:

| | KDE Plasma ("Joe User") | Hyprland ("Joe Developer") |
|---|---|---|
| Feels like | A classic desktop with menus and a settings app | A tiling desktop you drive from the keyboard |
| Good for | Office work, browsing, video calls | Code, terminals, containers, AI agents, remote desktop all day |
| Set up by | The T2 Ubuntu install, left as it is | This repository |

KDE never gets removed, so going back is always one logout away.

## What you get

### Battery and heat

The Intel iGPU drives the built-in display. The AMD GPU stays available because the external
display ports are wired to it, and it's held at its lowest power level. In Hyprland's default
battery mode nothing renders on it, so it idles at about 3 W instead of 8 W when apps used to
render on it (this Mac can't cut its power completely). Before you plug in a monitor, run
`hypr-gpu external`; `hypr-gpu battery` switches back. Turbo boost is off by default, which
keeps the machine cooler, quieter and longer on battery. Type `turbo-on` in a shell when you
need the speed. Compressed RAM swap (zram) and an early out-of-memory guard keep things
responsive when memory runs short, and clicking the battery icon lets you choose power saver,
balanced or performance.

### Audio

The MacBookPro16,1 speakers get the t2linux DSP: an FIR crossover, bass enhancement and a
limiter. It only touches the speakers, and you can switch it off again.

For headphones there's a 3D chain: AutoEq correction for your model, a binaural HRIR or room
response, and a short "stage" room. I tuned it on Therion and Hans Zimmer, so dense passages
keep their punch instead of turning into mush. Music headphones stay in stereo music mode, a
headset (AirPods, for me) takes calls, and the internal mic and speakers work for calls without
any of it.

### Developer tools

Node comes via nvm and Python tools via uv. You also get rootless Podman with Docker
compatibility, and virt-manager on KVM with nested virtualization. Chromium ships with a
matching `chromedriver`, for AI agents that drive a browser. VS Code, Zed, Sublime Text,
Positron, Quarto, OpenIDEA and the usual CLI tools are included too. The terminals and editors
share five colour themes, and Bash gets a grml-style prompt, a large shared history and
optional zsh-like suggestions via ble.sh.

### Everyday apps

If you're coming from Microsoft Office and Photoshop, the Craft suite is the part to look at.
WordCraft, GridCraft and DeckCraft cover documents, spreadsheets and slides, PdfCraft handles
PDFs, LightCraft is a Lightroom-style photo editor, DesignCraft does page layout and CADCraft
drawings. They follow the layout of the programs they replace, so Joe User doesn't have to
relearn much. They're young projects, so expect rough edges. LibreOffice is there too, with the
ribbon-style interface.

If you live in real Excel macros or a full Photoshop workflow (Joe Excelguru, Joe Artist), the
Craft apps won't cover everything. Run Windows in virt-manager for those; KVM makes it fast,
and the virtual TPM covers Windows 11.

The rest: Obsidian, Bitwarden, Slack, Discord, Zoom, Typora, Remote Desktop Manager, and
classic X apps like Xfe and NEdit.

### Remote access

Tailscale with a tray icon for picking your exit node. SSH starts at boot behind fail2ban. An
RDP server runs inside the Hyprland session, and it's only reachable over Tailscale.

## What it never touches

Disk encryption (LUKS/LVM), `fstab`, kernels, the bootloader and the initramfs are on a strict
no-go list (`.kiro/steering/protected-system-boundary.md`). Every package install goes through
a guard that blocks Snap/Flatpak, protected packages and removals. It also scans each package
for boot or encryption hooks before anything gets installed. The changes that need root are
small, and the dry run lists them first.

Snap and Flatpak are blocked on purpose. They pull in dependencies nobody here controls, and
some packages are built poorly for this kind of setup; Chromium as a Snap drags in GNOME
pieces, for example. Everything comes from Ubuntu's archive, a vendor's signed apt repository,
or a pinned and checksummed upstream release instead.

## Quick start

```sh
git clone https://github.com/norandom/intel-macbook-pro-linux.git ~/Source/t2-mac-kde
cd ~/Source/t2-mac-kde
sh bootstrap.sh                                               # uv + pinned pyinfra, no sudo

.venv/bin/pyinfra @local deploy.py --dry --use-sudo-password  # see every change first
.venv/bin/pyinfra @local deploy.py --use-sudo-password        # apply
```

Then log out and choose Hyprland at the login screen, or stay on KDE. Each part also runs on
its own, for example `.venv/bin/pyinfra @local tasks/speaker_dsp.py --use-sudo-password`. Run
everything as your normal user; only the system changes ask for your sudo password.

## Make it yours: one config file

Your own settings go in `~/.config/t2-mac-kde/config.toml`, never in the repository. The deploy
keeps a commented `config.example.toml` next to it with every option. Mine looks roughly like
this:

```toml
panel_scale = 1.6              # internal panel scale
desktop_left_reserve = 15      # my panel has dead pixel columns at the left edge
music_headphones = ["My QC35"] # Bluetooth name or MAC: these get the 3D preset
music_preset = "stage"         # plain | room | stage | room+ | auditorium
speaker_dsp = true             # false + re-run = plain speakers again
shell_blesh = true             # zsh-like suggestions in Bash
crash_upload = false           # no crash reports to Ubuntu
```

A one-off `--data key=value` on the command line overrides the file.

## Handy commands

These land in `~/.local/bin` or your shell. Most of the desktop ones are also on a key or a
bar button, so the command line is just the second way in.

Power and battery:

| Command | What it does |
|---|---|
| `turbo-on` / `turbo-off` / `turbo-status` | Intel turbo boost on or off (off after every boot) |
| `hypr-power-profile balanced` | power-saver, balanced or performance; the battery icon has the same menu |
| `hypr-brightness screen -5` | screen or keyboard light (`kbd`); one step below the minimum turns the panel off |
| `hypr-gpu battery` / `external` / `status` | Hyprland on the Intel GPU only, or with the AMD-driven external ports; applies at the next login (`--now` logs out) |

Audio:

| Command | What it does |
|---|---|
| `hypr-3d stage` | headphone preset: `plain`, `room`, `stage`, `plus` or `auditorium` |
| `hypr-3d off` / `hypr-3d on` | headphone effects off for a straight A/B comparison, and back on |
| `hypr-volume up` / `down` / `mute` / `micmute` | volume and mic keys with the on-screen popup |

Desktop (Hyprland):

| Command | What it does |
|---|---|
| `hypr-screenshot edit` | rectangle to `~/Screenshots`, then the Satty editor (SUPER+SHIFT+4) |
| `hypr-layout next` | dynamic or golden-ratio tiling (SUPER+L) |
| `hypr-nightmode next` | night filter: off, green or dark (the rabbit in the bar) |
| `hypr-deco win311` / `mac` | title bar style; `hypr-shadow on` / `off` for shadows |
| `hypr-kbd de` / `us` | keyboard layout (aliases `kbde`, `kbus`) |
| `hypr-findcursor` | flashes a huge pointer so you can find it (SUPER+SHIFT+C) |

Terminal and themes:

| Command | What it does |
|---|---|
| `hypr-termtheme next` | next of the five terminal/editor themes (SUPER+Y); or name one, e.g. `navy` |
| `k` | `kubectl` with completion |

System:

| Command | What it does |
|---|---|
| `t2-alerts` / `t2-alerts ack` / `t2-alerts log` | storage and service alerts, acknowledge them, NVMe health history |
| `hypr-rdp-control status` | the RDP server inside the Hyprland session (`start`, `stop`, `validate`) |
| `dev-disk-reclaim` | shows what caches and builds could be cleaned; `--apply` cleans them |

## Is it for you?

Probably not yet if:

- your Mac isn't a T2 MacBook Pro or Air from 2018–2020 (the MacBookPro16,1 is the one I know
  works);
- you depend on Touch ID, or on macOS-only apps with no Linux version;
- you can't make a backup first. This repository doesn't touch your disk layout, but the T2
  Linux install you start from does.

You don't have to give up macOS either. A T2 Linux install usually sits next to it. Keep macOS
around anyway, because SSD, T2 and EFI firmware updates only arrive through macOS.

## Docs

- Specs and steering: `.kiro/specs/`, `.kiro/steering/`
- Source port plan: `docs/source-port-plan.md`; backlog: `docs/backlog.md`
- Hibernate (needs a bigger swap, owner-run): `docs/hibernate-swap.md`

## Credits

Speaker DSP: [lemmyg/t2-apple-audio-dsp](https://github.com/lemmyg/t2-apple-audio-dsp) (MIT,
built on Asahi Linux's audio work). Headphone correction: [AutoEq](https://github.com/jaakkopasanen/AutoEq)
(MIT). HRIR: MIT KEMAR (Gardner & Martin). The optional auditorium room comes from the
[ASH Listening Set](https://github.com/ShanonPearce/ASH-Listening-Set) (CC BY-NC-SA 4.0); it's
downloaded to your machine and not redistributed here. T2 Linux itself is the work of the
[t2linux](https://wiki.t2linux.org/) community.
