# Customize when forking

Two ways to make the setup yours:

- **Config keys** in `~/.config/t2-mac-kde/config.toml` for everything that has a switch
  ([configuration.md](configuration.md)). No fork needed.
- **Repository files** for everything else. Fork, edit, re-run the task.

A few rules that save time:

- Files the deploy writes carry a `Managed by t2-mac-kde` marker and are rewritten on every run.
  Edit the source in the repository (`files/`, `templates/`), not the copy in `~/.config`.
- For the Hyprland, Waybar and theme files: if you delete the marker line from the copy, the
  deploy leaves that file alone from then on (with a warning). That works for a one-off tweak,
  but you lose updates to it.
- Hyprland also sources `~/.config/hypr/local.conf` near the end, and the deploy never writes
  it. Personal monitor lines, extra bindings or input overrides can go there without a fork.
- Clone the repository wherever you like. The tasks find their files relative to themselves.
- Run the tests after a change: `.venv/bin/python -m unittest discover -s tests`.

## Keyboard layout

The repository ships a German Mac layout with US as the second layout. Several places know that:

| Where | What to change |
|---|---|
| `files/desktop/hypr/input.conf` | `kb_layout = de,us`, `kb_variant = mac_nodeadkeys,` and `kb_options`. E.g. `kb_layout = fr,us` and `kb_variant = mac,` |
| `files/desktop/bin/hypr-kbd` | Knows the names `de` and `us` and maps them to layout 1 and 2. Rename them to match your list |
| `templates/desktop/waybar-config.jsonc.j2` | The `custom/kbd` badge falls back to `de` when no choice is stored |
| `files/shell/grml.bash` | The `kbde` / `kbus` aliases and the `setxkbmap` wrapper for Hyprland shells |
| `tasks/vendor_apps.py` | Writes `~/.xinputrc` with `run_im none`, so ibus (pulled in by Zoom) stays off. Change it if you need an input method, e.g. for CJK |

With a single layout, set `kb_layout = us`, empty `kb_variant`, and drop the `custom/kbd` module
from the bar.

Check the options too: `lv3:lalt_switch` makes Left Option the Mac Option key (Option+L = @ on
the German layout), and `altwin:swap_ralt_rwin` makes Right Option the Super key that all
bindings use. Drop the first if you'd rather have Left Option as plain Alt; drop the second and
Right Option is plain Alt again.

What the repository leaves alone:

- **KDE** has its own keyboard settings (System Settings, Keyboard). Set the layout there for
  Plasma.
- **The console, login screen and disk unlock prompt** take their layout from
  `/etc/default/keyboard` and the initramfs, set by the T2 install. Both are outside this
  repository on purpose ([safety.md](safety.md)).
- **RDP** follows the compositor's keymap, so it picks up your change by itself.

The screenshot (SUPER+SHIFT+4) and resize keys are bound by key position, not by character, so
they stay where they are on any layout.

Language packs are German plus English: `libreoffice-l10n-de`, `hunspell-de-de`, `hyphen-de` and
`mythes-de` in `LIBREOFFICE` (`tasks/office_apps.py`) and `firefox-devedition-l10n-de` in
`VENDOR_REPOS` (`manage/applications.py`). Swap them for yours (and the matching entries in
`OTHER` in `manage/applications.py`).

Re-run: `.venv/bin/pyinfra @local tasks/desktop.py --use-sudo-password` (and `tasks/shell.py`
for the aliases).

## Key bindings

| What | File |
|---|---|
| Window and app keys | the `keys` list at the top of `templates/desktop/bindings.conf.j2` |
| Mouse bindings | the `mouse` list in the same file |
| Hardware keys (brightness, volume, media), screenshots, find-pointer | `files/desktop/hypr/laptop.conf` |
| Personal extras without a fork | `~/.config/hypr/local.conf` |

Each `keys` entry is `(extra modifiers, key, dispatcher, argument, description)`, always with
SUPER in front. The template copies every entry into the one-shot Super submap (SHIFT+Print), so
you only add a key once. `hyprctl binds` lists what's active.

Apps are started through `~/.local/bin/hypr-launch`, which tells you with a notification when the
app is missing. Use it for new launch keys as well: `L ~ "hypr-launch yourapp"`.

## Adding or removing apps

| You want | Edit |
|---|---|
| An Ubuntu package | `NATIVE` in `manage/applications.py` (package, executable) |
| A vendor `.deb` | `VENDOR_DEBS` in `manage/applications.py` (package, version, URL, sha256, executable) |
| A vendor apt repo | key and `.list` in `files/vendor-apps/`, the key's sha256 in `VENDOR_REPOS` |
| A user-level tarball | `VENDOR_TARBALLS` plus the install steps in `tasks/vendor_apps.py` |
| A Craft app or OpenIDEA less | `ARTCRAFT` / `OPENIDEA_*` in `tasks/office_apps.py` |
| LibreOffice packages | `LIBREOFFICE` in `tasks/office_apps.py` |
| A CLI tool | `nix_tools_extra` in your config, or `DEFAULT_TOOLS` in `manage/nix_tools.py` |
| Fewer system CLI tools | the package list in `tasks/tools.py` |

Every install still goes through the package guard, so a package that pulls in Snap, touches the
kernel or boot, or removes something is refused. Removing an entry never uninstalls anything;
the deploy doesn't remove packages.

Each app also shows up in `manage/applications.py`'s `OTHER` table with a disposition. Keep it
in sync, and run the tests; `tests/test_vendor_apps.py` and friends check these tables.

## Waybar

Everything is in `templates/desktop/waybar-config.jsonc.j2` and `files/desktop/waybar/style.css`.

- **Which modules, in which order:** the `modules-left` and `modules-right` arrays near the top.
  Remove a name to drop a module, e.g. `custom/quota` if you don't use Claude or Codex.
- **Add a module:** add its name to an array and its block below. Any stock Waybar module
  works, e.g. `"temperature": { "format": "{temperatureC}°C" }`.
- **The web button** starts Vivaldi (`custom/web`). To use Chromium, set its `on-click` to
  `$HOME/.local/bin/hypr-launch chromium.desktop` and point `#custom-web` in `style.css` at a
  Chromium icon.
- **Files and terminal buttons:** `custom/files` and `custom/term`.
- **Colours and spacing:** `style.css`.
- **Numbers vs sparklines:** config `bar_graphs`, no edit needed.

Re-run `tasks/desktop.py`; it restarts Waybar in a running session when the bar changed.

## Palettes and themes

The five terminal and editor palettes are named in two places, and each app has its own files:

| What | Where |
|---|---|
| Palette names | `THEMES` in `tasks/themes.py`; `PROFILES` and `FONTS` in `files/themes/bin/hypr-termtheme` (`default` is cobalt) |
| Terminator | `files/themes/terminator/config` (one profile per palette) |
| foot, Ghostty | `files/themes/foot/themes/<name>.ini`, `files/themes/ghostty/themes/<name>` |
| btop, Claude Code | `files/themes/btop/<name>.theme`, `files/themes/claude/<name>.json` |
| Sublime Text, VS Code and Positron | `files/themes/sublime/`, `files/themes/vscode/debian-hypr-themes/` |
| Neovim | `files/themes/nvim/plugin/debian-hypr-theme.lua` |

To add a palette, add the name to both lists and a file for each app. To change one, edit its
files. Re-run `tasks/themes.py`.

The desktop's own colours are separate from the palettes:

| What | Where |
|---|---|
| Borders, gaps, blur | `files/desktop/hypr/looknfeel.conf`, `borders.conf` |
| Title bars | `files/desktop/hypr/decorations-win311.conf`, `decorations-mac.conf` |
| Bar | `files/desktop/waybar/style.css` |
| Notifications, launcher | `files/desktop/mako/config`, `files/desktop/fuzzel/fuzzel.ini` |
| Per-host colour | config `fleet_hosts`, `[decor_colors]`; logic in `manage/desktop_hostcolor.py` |

## Disabling a whole task

Remove its line from the tuple in `deploy.py`. The full deploy then skips it; you can still run
it on its own. Removing a task doesn't undo what it already set up.

Watch the dependencies:

| If you remove | Then also |
|---|---|
| `desktop` | `audio_effects` and `rdp` start with the Hyprland session target it creates; they'd install but never run |
| `remote_access` | remove `rdp` too: the firewall that limits port 3389 to Tailscale lives in `remote_access` |
| `node` | `shell` needs nvm's Node for its npm tools |
| `nix_tools` | set `nix_tools = []` in your config, so `apps` and `containers` install their release binaries instead |
| `vendor_apps` | `themes` simply skips the editors that aren't there |
| `cpu_mitigations` | `tests/test_cpu_mitigations.py` checks that it's listed; update that test |

`tools` also installs `config.example.toml`, so keep it unless you have your own copy.

## Re-running one task

```sh
.venv/bin/pyinfra @local tasks/<name>.py --dry                 # what would change
.venv/bin/pyinfra @local tasks/<name>.py --use-sudo-password   # apply
```

The task names are the ones in `deploy.py`. Each task runs fine on its own, apart from the
order notes in
[configuration.md](configuration.md#running-the-deploy-or-one-task).
