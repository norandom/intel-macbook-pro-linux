# Desktop: Hyprland next to KDE

`tasks/desktop.py` sets up a Hyprland session using Ubuntu's own packages (Hyprland 0.53 with
the hyprbars plugin, uwsm, Waybar, mako, fuzzel, hyprlock, hypridle). Pick
**Hyprland (uwsm-managed)** at the login screen. KDE Plasma stays installed and unchanged, and
SDDM isn't reconfigured. KDE is dormant: Kubuntu is the base for its support lifetime, and the
repo puts no work into the KDE session beyond not breaking it.

## Windows: dynamic by default, tiling when needed

Hyprland is usually set up as a tiling desktop. This one isn't. The default layout, `dynamic`,
floats every new window and centres it, and `hypr-windows` remembers where each application
was and how big. Windows get title bars (the hyprbars plugin) with buttons to close and
maximise, so the laptop works the way you'd expect without learning a tiling workflow first.

Tiling is there for the moments it helps, such as a terminal next to an editor, or several
agent dashboards side by side:

- SUPER+T switches the focused window between floating and tiled.
- SUPER+L cycles the layout mode: `dynamic` (floating), then the golden-ratio tilings
  `golden-h`, `golden-v` and `golden-spiral`, then back to `dynamic`. The Waybar layout button
  does the same.

The modes live in `files/desktop/hypr/layout-*.conf`.

## How it lives next to KDE

- Everything the Hyprland session needs (Waybar, the window worker, clipboard history,
  EasyEffects, the Tailscale tray, the secret service, the RDP server) hangs off one user
  target, `hypr-desktop.target`. Hyprland starts it, so none of it runs in a KDE login.
- `~/.config/gtk-3.0/settings.ini` is shared with KDE, so the deploy only writes it when it
  doesn't exist yet.
- Chromium-based and Electron apps use the same password store in both sessions (KDE Wallet by
  default, config `password_store`), so saved passwords show up on either side.
- The deploy only rewrites files that carry its `Managed by t2-mac-kde` marker. A file of yours
  at the same path is left alone, with a warning.

## Keyboard

The layout lives in `files/desktop/hypr/input.conf` (copied to `~/.config/hypr/input.conf`):

| Setting | Value | Effect |
|---|---|---|
| `kb_layout` | `de,us` | German Apple layout first, US second |
| `kb_variant` | `mac_nodeadkeys,` | German without dead keys |
| `kb_options` | `compose:caps` | Caps Lock is the Compose key |
| | `shift:both_capslock_cancel` | both Shifts together toggle Caps Lock |
| | `altwin:swap_ralt_rwin` | Right Option acts as Super |
| | `lv3:lalt_switch` | Left Option is the Mac Option key (Option+L = @, Option+5/6 = [ ]) |

`hypr-kbd de` / `hypr-kbd us` (or `kbde` / `kbus` in a Hyprland shell) switches the active
layout, and the `⌨ DE` badge in the bar toggles it. The choice survives config reloads. KDE keeps
its own keyboard settings in System Settings; this repository doesn't change them.

To change the layout for your fork, see [forking.md](forking.md#keyboard-layout).

An external Apple Magic Keyboard works as is (kernel driver `hid_apple`). If you want it to behave
differently from the built-in one, the safe route is a Hyprland `device { name = ...; kb_options = ... }`
block for that keyboard only. The driver's module options (`fnmode`, `swap_opt_cmd`) would also
change the built-in T2 keyboard and need an initramfs rebuild, so this repository doesn't use them.

## Keys

SUPER is Right Option on the Apple keyboard. On a keyboard without a spare Super key,
SHIFT+Print arms a one-shot Super for the next key (the bar shows a `SUPER` badge).

| Key | Action |
|---|---|
| SUPER+Return | Terminal (Terminator in the current theme) |
| SUPER+SHIFT+Return | xfce4-terminal (asks before pasting several lines) |
| SUPER+Space | Launcher (fuzzel) |
| SUPER+A | Application menu (Windows 95 style; right-click on the empty desktop works too) |
| SUPER+E | File manager (Xfe) |
| SUPER+V | Clipboard history |
| SUPER+W | Close window |
| SUPER+F / SUPER+SHIFT+F | Full screen / maximize |
| SUPER+T | Floating or tiling |
| SUPER+L | Next layout mode (dynamic, golden-h, golden-v, golden-spiral) |
| SUPER+Tab | Next window, raised |
| SUPER+arrows | Move focus |
| SUPER+M | Show minimized windows |
| SUPER+G / SUPER+P | Glass window / stay on top |
| SUPER+Y | Next terminal and editor theme |
| SUPER+Escape | Power menu (lock, suspend, log out, reboot, shut down) |
| SUPER+SHIFT+M | Log out |
| SUPER+SHIFT+4 or SUPER+SHIFT+S | Screenshot of a rectangle, then the Satty editor |
| SUPER+SHIFT+CTRL+S | Screenshot of the screen, then Satty |
| SUPER+SHIFT+X | Rectangle screenshot, no editor |
| SUPER+SHIFT+C | Flash a huge pointer so you can find it |
| SUPER+left drag / right drag | Move / resize a window |

The two keys right of `0` resize the active window (narrower, wider; with SHIFT shorter,
taller). Brightness, keyboard light, volume, mic mute and media keys work as on macOS.
Screenshots land in `~/Screenshots` and on the clipboard.

The bindings come from `templates/desktop/bindings.conf.j2`; the laptop keys and screenshot
keys from `files/desktop/hypr/laptop.conf`.

## Trackpad

The trackpad uses Hyprland's defaults. To change how it feels:

```sh
hypr-touchpad                 # current speed and scroll speed
hypr-touchpad speed +0.1      # faster pointer (-1 .. 1, default 0)
hypr-touchpad scroll 0.8      # slower scrolling (0.1 .. 3, default 1)
hypr-touchpad reset
```

It applies right away and only to the internal trackpad, so an external mouse keeps its own
settings. The values are saved to `~/.config/hypr/touchpad.conf`, which the deploy creates once
and then leaves to you.

## Waybar

The top bar is rendered from `templates/desktop/waybar-config.jsonc.j2`, styled by
`files/desktop/waybar/style.css`.

Left: Apps menu, quick launchers (Xfe, Terminator, web browser), layout mode, window list.
Right, in order:

| Module | Shows | Click |
|---|---|---|
| AI quota | weekly quota left for Claude and Codex | refresh |
| CPU, memory, network | usage in percent, `↓ ↑` rates; sparklines with `bar_graphs = true` | CPU opens btop |
| Audio | speaker icon, slider on hover | mute; scroll changes volume |
| Backlight | screen brightness | scroll changes it |
| Power profile | current profile | power-saver, balanced, performance |
| Battery | charge, watts and time left in the tooltip | power profile menu |
| Tray | Wi-Fi, Bluetooth, Tailscale, other apps | |
| Clipboard | history | pick; right-click wipes it |
| Rabbit | night filter | off, green, dark |
| Theme | terminal theme | next; right-click previous |
| `⌨ DE` | keyboard layout | switch DE and US |
| Clock | weekday and time | date and week number |
| Power | | lock, suspend, log out, reboot, shut down |

The web launcher starts Vivaldi, which `tasks/vendor_apps.py` installs from Vivaldi's own repo.
To use another browser there, see [forking.md](forking.md#waybar).

With `desktop_left_reserve` set, a black strip of that many pixels at the left panel edge is
kept free of windows. I need it for a few dead pixel columns.

## Display and GPUs

- `panel_scale` sets the internal panel scale (`auto` lets Hyprland decide; I use 1.6).
  Border and title bar sizes snap to whole pixels at fractional scales, so edges don't flicker.
- External monitors use their preferred mode. Your own monitor lines go in
  `~/.config/hypr/local.conf`, which is sourced near the end and never written by the deploy.
- The AMD GPU drives the external ports. In `hypr-gpu battery` mode (the default) Hyprland only
  uses the Intel GPU and external displays stay dark; `hypr-gpu external` brings them in at the
  next login. See [power.md](power.md#gpu-modes).

## Idle, dim and lock

From `files/desktop/hypr/hypridle.conf`:

| After | What happens |
|---|---|
| 5 min | Screen dims to 10 % (only if it's brighter); activity restores the previous brightness |
| 10 min | Lock (hyprlock) |
| 11 min | Panel off |
| Before suspend | Always locks first |

The clipboard history (cliphist) lives in RAM only and is wiped every night at 01:00. The timer
catches up after resume, so if the machine slept through 01:00 the wipe runs as soon as it
wakes. Logging out or shutting down clears it as well.

Lid close is still handled by logind, as on a stock install.

## Look

- Title bars: `hypr-deco win311` or `hypr-deco mac`; shadows: `hypr-shadow on` / `off`.
  The config keys `decorations_style` and `window_shadows` only set the first value; after that
  the commands decide.
- Night filter: `hypr-nightmode next` (off, green, dark).
- Pointer: `cursor_theme = "t2-highvis"` gives a large white arrow with a red outline;
  `cursor_size` makes it bigger.
- Title bar and border colour come from the hostname, so different machines look different
  (`fleet_hosts`, `[decor_colors]`).
- Five palettes (cobalt, navy, fixedsys, cream, petrol) are shared by Terminator, foot,
  Ghostty, btop, Neovim, Sublime Text, VS Code, Positron and Claude Code. `hypr-termtheme next`
  or SUPER+Y switches them together.

## Change it

| You want to change | Edit |
|---|---|
| Keyboard layout | `files/desktop/hypr/input.conf`, plus `hypr-kbd` ([forking.md](forking.md#keyboard-layout)) |
| Key bindings | `templates/desktop/bindings.conf.j2`, `files/desktop/hypr/laptop.conf` |
| Bar modules | `templates/desktop/waybar-config.jsonc.j2`, `files/desktop/waybar/style.css` |
| Idle timeouts | `files/desktop/hypr/hypridle.conf` |
| Colours, gaps, blur | `files/desktop/hypr/looknfeel.conf` |
| Monitors, local tweaks | `~/.config/hypr/local.conf` (yours, never overwritten) |
| Scale, pointer, bar graphs | config keys, see [configuration.md](configuration.md#desktop) |

Then re-run `.venv/bin/pyinfra @local tasks/desktop.py --use-sudo-password`. A running Hyprland
reloads by itself when its config changed.
