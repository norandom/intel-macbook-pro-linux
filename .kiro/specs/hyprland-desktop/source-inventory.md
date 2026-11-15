# Source Desktop Inventory

Repository: `norandom/hyperland-forky-worker-vm`; revision
`a1c09ec3f02a98b7c6a4641f907108a2ad080993`. Blob identities below survive loss of the temporary checkout.

| Source path | Blob SHA | Intended disposition |
| --- | --- | --- |
| `files/bin/hypr-agent-quota` | `10e0bfaf1fb90871c52ee5c61e6f6c3483c24160` | Backport to native0.53 config/IPC; retain source behavior |
| `files/bin/hypr-appmenu` | `d00b518677eaad7c97bc5848155d39d596b08c0c` | Backport to native0.53 config/IPC; retain source behavior |
| `files/bin/hypr-clip-bridge` | `5d33300e5716b6cc2d7d45f876ff46da14d61ebc` | Backport to native0.53 config/IPC; retain source behavior |
| `files/bin/hypr-cliphist` | `274f4070f12dfabda6d1e9ca742c9051f7770db7` | Backport to native0.53 config/IPC; retain source behavior |
| `files/bin/hypr-deco` | `25d56076c2248b0f230dc28151d066e4fa51baca` | Backport to native0.53 config/IPC; retain source behavior |
| `files/bin/hypr-glass` | `16182426bf3fb09066a08fff7c7665c29528cf1a` | Backport to native0.53 config/IPC; retain source behavior |
| `files/bin/hypr-kbd` | `93bdbf7f2fa00655bb2d894fb471ae456ee0cdcb` | Backport to native0.53 config/IPC; retain source behavior |
| `files/bin/hypr-launch` | `cd05b59eb1bb7bb56d30fb598d0b1b5989f387d3` | Backport to native0.53 config/IPC; retain source behavior |
| `files/bin/hypr-layout` | `80d7d148cb72d69f9eb546064b02ebe4b0fa8d0d` | Backport to native0.53 config/IPC; retain source behavior |
| `files/bin/hypr-licenses` | `a7d9933fe2bc7d5707b098a62faa7bdc0eb445a3` | Delegated: application/private-artifact policy; no credentials copied |
| `files/bin/hypr-nightmode` | `4a8435d86d6e91b92619ed15d102720d2ba94ffb` | Backport to native0.53 config/IPC; retain source behavior |
| `files/bin/hypr-pin` | `af3ed3609df7631d1cc405681c36b7f551bcbbe1` | Backport to native0.53 config/IPC; retain source behavior |
| `files/bin/hypr-shadow` | `3b7d43435157790e4fa5650539c015c34a27a0c2` | Backport to native0.53 config/IPC; retain source behavior |
| `files/bin/hypr-sparkline` | `217939d4aff39d08cddd31c89d8cc37159ec28ad` | Backport to native0.53 config/IPC; retain source behavior |
| `files/bin/hypr-term` | `4c0c3c475549fb4998873712f33e44d4cb4990d0` | Delegated: coordinated-themes; consume CLI/state only |
| `files/bin/hypr-termtheme` | `de52dc0a78e2bd16ab9265fe23fc3c114297d3f7` | Delegated: coordinated-themes; consume CLI/state only |
| `files/bin/hypr-xfonts` | `b58b022f3ce782380c6c2131089edb0e61f2788a` | Delegated: desktop-fonts; call /usr/local/bin/hypr-xfonts |
| `files/fuzzel/fuzzel.ini` | `bae61a05757fbb30361929ca54e2530c556cca39` | Backport to native0.53 config/IPC; retain source behavior |
| `files/gtk-3.0/gtk.css` | `060a94f39f5e26bfa973be1b4b35131fc411be0f` | Delegated: coordinated-themes scoped Terminator tab CSS/import |
| `files/hypr/aerosnap.lua` | `8987a51d2df8cff2bf5c9b69cc784061e03d0607` | Backport to native0.53 config/IPC; retain source behavior |
| `files/hypr/autostart.lua` | `2b7189c9d42ef6f660717d4c562adb1ed7e9acc1` | Adapt session lifecycle; omit VM initial lock and RDP assumption |
| `files/hypr/bindings.lua` | `d21f82a44865273530143cb6899581e1d9f45ddd` | Backport to native0.53 config/IPC; retain source behavior |
| `files/hypr/cursorzone.lua` | `0ac00f014bfea60521fb6fa5dd4a2aa66e7f38b9` | RDP-specific behavior; RDP integration owns remote cursor transitions |
| `files/hypr/decorations.lua` | `961afc403fb4bb10e8bc72a954d454eefa0de260` | Backport to native0.53 config/IPC; retain source behavior |
| `files/hypr/hyprland.lua` | `9c172e8ca42b1b63e2bcf0b36de71ed7f851082d` | Backport to native0.53 config/IPC; retain source behavior |
| `files/hypr/hyprlock.conf` | `014c414ac062c83d6d297fb74b653002308a74df` | Reuse/adapt explicit lock only; no initial RDP-presence lock |
| `files/hypr/layouts.lua` | `4979853a7734d939180652ac55a91ca2d7c6f3e2` | Backport to native0.53 config/IPC; retain source behavior |
| `files/hypr/looknfeel.lua` | `2b44c62582da1b865ebd753446733c4fd0b49ed2` | Backport to native0.53 config/IPC; retain source behavior |
| `files/hypr/shaders/night-dark.glsl` | `b42ca62ce9fdab5a0bc3fccebc857410d55b601c` | Backport to native0.53 config/IPC; retain source behavior |
| `files/hypr/shaders/night-green.glsl` | `b201008007b74e85c1b2f4a487a41e526f507f98` | Backport to native0.53 config/IPC; retain source behavior |
| `files/mako/config` | `da9126a97a573770a634194c87a85a83b615bd3b` | Backport to native0.53 config/IPC; retain source behavior |
| `files/waybar/power.png` | `85c15738dd4125bc571cf60a7dd47d0415b192f4` | Backport to native0.53 config/IPC; retain source behavior |
| `files/waybar/style.css` | `8d52383e490a1208a0b44869d94c84d711c5e8c3` | Backport to native0.53 config/IPC; retain source behavior |
| `files/xfe/xferc` | `d0f99f00df43e57909a702623ebc46fb500c24f5` | Backport to native0.53 config/IPC; retain source behavior |
| `group_data/all.py` | `1e032b25e99104655931f4199fb55974a65ae598` | Source defaults evidence; retain exact session keyboard mapping; omit VM defaults |
| `tasks/desktop.py` | `f74fc7b12b6950de73abf60ccea3aab48712e042` | Source orchestration evidence only; split app/font/theme owners; no direct deploy copy |
| `templates/gtk-3.0/settings.ini.j2` | `9ccaa152c028003b411a0e3834edc2ec60c4f949` | Backport to native0.53 config/IPC; retain source behavior |
| `templates/hypr/input.lua.j2` | `4ea92e793696b03b6dc7c9a606180561d8838e2a` | Backport to native0.53 config/IPC; retain source behavior |
| `templates/hypr/monitors.lua.j2` | `a346a3786c53ae29df2d36e194188fde89a707f4` | Adapt physical monitors; exclude RDP modecache/VM output and input disabling |
| `templates/waybar/config.jsonc.j2` | `86cfbbfa3b843c1d8a4c5c2573b275d3a91e1037` | Backport to native0.53 config/IPC; retain source behavior |
| `tools/hostcolor.py` | `6316f7360ea8e6118c4b9dcfa80c418c6c4a3a55` | Backport to native0.53 config/IPC; retain source behavior |

## Full bar coverage

Source template owns both graph and numeric variants. Required modules:
custom/menu, custom/files, custom/term, custom/web, custom/layout, wlr/taskbar,
clock, custom/quota, custom/cpu/custom/mem/custom/net or cpu/memory/network,
group/audio with pulseaudio and pulseaudio/slider, tray, hyprland/submap,
custom/cliphist, custom/nightmode, custom/termtheme, custom/kbd, custom/power.

The pulseaudio modules talk to preserved pipewire-pulse; mute uses wpctl.
No plasma-pa dependency. Source power.png is retained with its pinned blob
identity; resolve destination paths instead of assuming Debian install paths.

## Application menu artwork

Source optional Win3.1 icons use mRB0/many-windows-3.1-icons-in-png-format at
`c351992eadee522c585d2ef87f08fe0e168a80ca`; source offers application icons
when absent. Keep these external Microsoft-derived icons optional and record
artifact provenance/permission disposition; do not silently make them required.
Source menu behavior and included power artwork remain required.

## Required adaptations

Hypr-launch currently flattens argv into one string; the port must preserve
argument boundaries and desktop-entry semantics, including spaces/quotes,
without shell/Lua injection. Config reload must not kill launched applications.
Quota reads existing user credentials only for the designated source provider;
no token material belongs in manifests, logs, receipts or fixtures. Clipboard
history uses runtime-only storage; no /etc/fstab or tmpfs mount provisioning.
GTK/Xfe initial seed must not overwrite subsequent user preference changes.
Lua configuration is translated to .conf fragments; callbacks/timers become a
session IPC worker. This is a backport of current behavior, not recovery of an
old .conf file (the source repository has no such known predecessor).
No app, theme, RDP, resource-policy or font implementation is claimed here.
