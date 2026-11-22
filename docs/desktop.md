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

The deploy builds hyprbars itself (pinned upstream 0.53.0 plus
`files/desktop/hyprbars/hyprbars-0.53.0-t2-input.patch`, against `hyprland-dev`) into
`~/.local/lib/t2-mac-kde/hyprbars`. Ubuntu's packaged plugin routes some title-bar clicks to the
wrong window; see `docs/known-issues.md`. After a Hyprland update the package plugin is used
until the next desktop deploy rebuilds ours.

Some apps draw their own title bar on Wayland: GTK always does, and Tauri apps such as Deckle
add their own header bar, which CSS can't remove. Running them under XWayland would drop it but
scales them by whole numbers only (2x on the 1.6 panel: too big). List their window classes
(`hyprctl clients`) in `own_titlebar_apps = ["Deckle"]`: they keep their own bar and get no
hyprbars bar on top (`~/.config/hypr/apps.conf`). Hyprland ignores an app's own move request,
so move these windows with SUPER+drag; SUPER+right-drag resizes. Hyprland also ignores an app's own
minimize request; our hyprbars build hooks that request and parks the window like the
taskbar does, so their minimize button works (after the deploy and a re-login).

Tiling is there for the moments it helps, such as a terminal next to an editor, or several
agent dashboards side by side:

- SUPER+T switches the focused window between floating and tiled.
- SUPER+L cycles the layout mode: `dynamic` (floating), then the golden-ratio tilings
  `golden-h`, `golden-v` and `golden-spiral`, then back to `dynamic`. The Waybar layout button
  does the same.

The modes live in `files/desktop/hypr/layout-*.conf`.

## How it lives next to KDE

The Ubuntu packages of Waybar, mako, hypridle and hyprpolkitagent enable themselves for every
graphical session, so they also came up inside Plasma (Hyprland's bar, notifications, idle
rules and polkit agent). The deploy adds a per-user drop-in
(`~/.config/systemd/user/<unit>.d/t2-hyprland-only.conf`) that starts them only when
`XDG_CURRENT_DESKTOP=Hyprland`; the package links stay as they are.

- Everything the Hyprland session needs (Waybar, the window worker, clipboard history,
  EasyEffects, the Tailscale tray, the secret service, the RDP server) hangs off one user
  target, `hypr-desktop.target`. Hyprland starts it, so none of it runs in a KDE login.
- `~/.config/gtk-3.0/settings.ini` is shared with KDE, so the deploy only writes it when it
  doesn't exist yet.
- Chromium-based and Electron apps use the same password store in both sessions (KDE Wallet by
  default, config `password_store`), so saved passwords show up on either side. At login
  `hypr-wallet-check` makes sure `kwalletd6`, which those apps talk to, really returns stored
  passwords, and restarts it when it hands back empty ones. Otherwise a browser like Vivaldi
  reports a broken key store and offers to throw away its saved logins. If that dialog ever
  shows anyway: choose Quit, run `pkill kwalletd6`, start the browser again.
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

KDE gets the same keyboard: German Mac without dead keys plus US, the same Option and Super
keys, key repeat and NumLock (`manage/kde_input.py`, written to `kxkbrc` and `kcminputrc`;
only these keys). The KDE values are tested against `files/desktop/hypr/input.conf`, so the two
sessions stay the same.

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
| SUPER+M | Centered picker: select a minimized window to restore (Esc cancels) |
| SUPER+G / SUPER+P | Glass window / stay on top |
| SUPER+Y | Next terminal and editor theme |
| SUPER+Escape | Power menu (lock, suspend, log out, reboot, shut down) |
| SUPER+SHIFT+M | Log out |
| SUPER+SHIFT+4 or SUPER+SHIFT+S | Screenshot of a rectangle, then the Satty editor |
| SUPER+SHIFT+CTRL+S | Screenshot of the screen, then Satty |
| SUPER+SHIFT+X | Rectangle screenshot, no editor |
| SUPER+SHIFT+C | Flash a huge pointer so you can find it (and bring it back from the virtual RDP output) |
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
hypr-touchpad tapdrag on      # double-tap-and-drag (default off)
hypr-touchpad reset
```

Double-tap-and-drag is off by default. With it on, libinput ends the drag a moment after you
lift your finger, and the title bars can miss that late release: the window keeps following the
pointer. Press the trackpad down to drag instead, as on macOS. Tap to click stays on.

It applies right away and only to the internal trackpad, so an external mouse keeps its own
settings. The values are saved to `~/.config/hypr/touchpad.conf`, which the deploy creates once
and then leaves to you.

## Waybar

Click a window in the task list to bring it forward (or restore it). Clicking the
already-active window minimizes it; middle-click still closes it. Focus follows
explicit clicks, not pointer hover, and restoring a window does not warp the pointer.

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
| Moon / sun | night shift (`night_shift = true`): warm after sunset, period and temperature in the tooltip | pause / resume |
| Rabbit | screen filter | centered mode picker; right-click off |
| Theme | terminal theme | next; right-click previous |
| `⌨ DE` | keyboard layout | switch DE and US |
| Coffee cup | keep awake (highlighted = on) | toggle automatic dim / lock / screen off |
| Clock | weekday and time | date and week number |
| Power | | lock, suspend, log out, reboot, shut down |

The battery and power-profile buttons open the overlay picker at the top right.
Click outside it or press Esc to dismiss; the current profile has a check mark.

The web launcher starts Vivaldi, which `tasks/vendor_apps.py` installs from Vivaldi's own repo.
To use another browser there, see [forking.md](forking.md#waybar).

With `desktop_left_reserve` set, a black strip of that many pixels at the left panel edge is
kept free of windows. I need it for a few dead pixel columns.
KDE gets the same black strip from `t2-leftstrip` (`t2-kde-leftstrip.service`, KDE sessions
only), sized for KDE's own scale so it covers the same physical pixels. Plasma keeps windows,
desktop icons, its panels and the start menu clear only of its own panels, so at each KDE login
the helper makes sure of an empty Plasma panel of that width on the left and draws black over
it. A bottom panel still at Plasma's full-width default gets an offset of 11 px: the start
menu opens that far left of the panel's offset, and would otherwise cover the strip. A bottom
panel you have set up yourself is left alone.

## Display and GPUs

- `panel_scale` sets the internal panel scale (`auto` lets Hyprland decide; I use 1.6).
  Border and title bar sizes snap to whole pixels at fractional scales, so edges don't flicker.
- X11 apps (Xfe, NEdit, xpdf, x3270) are sharp at fractional scales: Xwayland draws them at
  the panel's real pixels (`force_zero_scaling`), and `hypr-xscale` sets their DPI at login to
  96 × the panel scale (154 at 1.6): `Xft.dpi`, scaled NEdit and x3270 fonts, Xfe's `screenres`.
  `hypr-xscale --print` shows the values. A font saved in NEdit's preferences wins; Xfe's DPI
  is reset at every login. An X11 app that ignores `Xft.dpi` comes out small.
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

Click the coffee cup beside the clock to keep the screen awake; click again to restore
these idle timers. It uses [Waybar's native idle inhibitor](https://github.com/Alexays/Waybar/wiki/Module:-Idle-Inhibitor),
which hypridle honors by default. The toggle starts off when Waybar starts or restarts.
Manual locking and locking before suspend still work; lid-close behavior is unchanged.

The clipboard history (cliphist) lives in RAM only and is wiped every night at 01:00. The timer
catches up after resume, so if the machine slept through 01:00 the wipe runs as soon as it
wakes. Logging out or shutting down clears it as well.

Lid close is handled by logind: it suspends, as on a stock install, or hibernates with
`lid_close = "hibernate"` and `hibernate = true` ([configuration.md](configuration.md)).

## Look

- Title bars: `hypr-deco win311` or `hypr-deco mac`; shadows: `hypr-shadow on` / `off`.
  The config keys `decorations_style` and `window_shadows` only set the first value; after that
  the commands decide.
- Screen filter: click the rabbit for a centered picker (current mode marked),
  or use `hypr-nightmode next` (off, green, dark, grayscale, monochrome, warmwhite).
  Grayscale keeps smooth shades and caps white at approximately RGB 199/199/199; monochrome uses four charcoal-to-gray-green shades for a 1990s LCD look,
  with subtle static dithering only around shade boundaries.
  Your selection persists across login, reboot and config reload through generated
  `state.conf`; deployment preserves the saved choice.
  Right-click the rabbit to turn filters off; `hypr-nightmode grayscale` and
  `hypr-nightmode monochrome` select either directly.
  `hypr-nightmode warmwhite` dims and warms the white content of each pixel toward muted cream:
  white inside large white areas (browser pages) becomes approximately RGB 219/211/193, white text
  and lines on dark or coloured backgrounds (terminals) approximately RGB 173/167/152, including
  anti-aliased glyph edges. Darker tones and saturated colors are preserved; this is selective
  highlight warming rather than an overall color-temperature shift.
- Night shift, like f.lux: with `night_shift = true`, gammastep warms the screen after sunset
  and back after sunrise, fading through dusk and dawn. It follows the sun at a fixed place:
  `night_shift_location = "lat:lon"`, or by default the city of your timezone (Europe/Berlin:
  Berlin), looked up locally, nothing is sent anywhere. Temperatures: `night_shift_day` (6500 K)
  and `night_shift_night` (4500 K). The moon on the bar pauses it; it runs only in the Hyprland
  session (`hypr-gammastep.service`). It combines with the rabbit filter.
- Pointer: `cursor_theme = "t2-highvis"` gives a large white arrow with a red outline;
  `cursor_size` makes it bigger.
- Title bar and border colour come from the hostname, so different machines look different
  (`fleet_hosts`, `[decor_colors]`).
- Five palettes (cobalt, navy, fixedsys, cream, petrol) are shared by Terminator, foot,
  Ghostty, btop, fish, the Starship prompt, Neovim, Sublime Text, VS Code, Positron and Claude Code. `hypr-termtheme next`
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
