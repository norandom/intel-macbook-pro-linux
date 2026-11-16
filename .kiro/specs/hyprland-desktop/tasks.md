# Implementation Checklist: hyprland-desktop (native Hyprland 0.53 backport)

Deploy (owner-run): `.venv/bin/pyinfra @local tasks/desktop.py` (preview: `--dry`).
Then pick "Hyprland (uwsm-managed)" at the unchanged SDDM login screen.

## Implemented
- [x] Packages through `install_packages(PackageRequest(..., source="ubuntu"))`: hyprland 0.53.3,
      hyprland-plugin-hyprbars 0.53.0, uwsm, portals (hyprland, gtk), xwayland, waybar, mako, fuzzel,
      hyprlock, python3-gi/GTK3/gtk-layer-shell, wl-clipboard, cliphist, jq, adwaita-icon-theme
- [x] Session entry comes from the hyprland package (`hyprland-uwsm.desktop`); deploy only checks it is
      dpkg-owned. No SDDM, autologin, KDE, audio, boot or storage changes
- [x] Lua -> 0.53 conf backport in `files/desktop/hypr/` (verified `Hyprland 0.53.3 --verify-config`
      for all 16 layout x style x shadow combinations: "config ok")
- [x] Original decorations first: mac / win311 hyprbars bars (heights, fonts, alignment, button order,
      colours, glyphs, double-click maximize), oil-gradient host-colour borders (source hostcolor)
- [x] hyprbars path discovered from `dpkg-query -L hyprland-plugin-hyprbars` (`hypr-desktop-state`)
- [x] Switches: hypr-deco, hypr-shadow, hypr-layout (4 modes + live float/tile of existing windows),
      hypr-glass, hypr-pin (address-pinned, 0.53 setprop/getprop), hypr-nightmode (keyword shader,
      re-applied on reload), hypr-kbd (de/us, re-applied on reload)
- [x] Keyboard policy: de,us / mac_nodeadkeys / source option string (Option+L = @)
- [x] Bindings from source incl. one-shot Super submap (SHIFT+Print, mirrored binds, Escape/catchall)
- [x] hypr-windows worker (replaces Lua timers/events): dynamic per-class geometry memory + cascade,
      X3270 excluded, keep title bars below the bar, monitor-resize scaling, aero snap (style-aware
      bar height), desktop right-click -> appmenu
- [x] Waybar (all source modules, graph/numeric branches), style, power artwork; Mako; Fuzzel
      (`terminal=hypr-term -x`, uwsm launch-prefix); appmenu (+ Lock entry); sparkline; agent quota
- [x] hypr-launch: argv-preserving `uwsm app --` via Hyprland exec; missing apps notify, exit 127
- [x] Clipboard: cliphist in $XDG_RUNTIME_DIR (200 entries, Bitwarden/sensitive excluded), wipe on
      service stop + 01:00 timer, STRING->UTF-8 bridge
- [x] Services wanted only by `hypr-desktop.target` (started by Hyprland exec-once; BindsTo
      graphical-session.target) - nothing starts in KDE logins
- [x] `hypr-session status --json` (explicit instance only, exit 2 unavailable) and `hypr-session xfonts`
      (calls desktop-fonts' /usr/local/bin/hypr-xfonts when present)
- [x] Theme seam: reads ~/.local/state/terminator-profile read-only; hypr-term/hypr-termtheme by name
- [x] Seeds only when absent: GTK settings.ini (KDE's exists -> skipped), xferc, xdg-terminals.list;
      other owned files skip unmanaged user files (marker check)
- [x] tests/test_desktop.py (geometry, bindings mirror, hyprbars keys, state renderer, launch quoting,
      session status, boundaries)

## Deferred / needs owner live check
- [ ] Xfe not installed: Ubuntu xfe `Conflicts: im-config` (kubuntu-desktop dependency) - owner to pick a file manager
- [ ] Live session: hyprbars buttons/actions, aero snap, geometry memory, one-shot Super (verify-config skips plugin keys)
- [ ] Physical keys: Option+L=@, brackets/braces/|/\/EUR/~, Right Option=Super, de/us switch
- [ ] Audio slider/mute on the T2 PipeWire route; notifications; portals; screen shaders compile
- [ ] Clean logout leaves no services/env (uwsm cleanup of imported HYPRLAND_INSTANCE_SIGNATURE)
- [ ] Xwayland restart re-registration of fonts (only initial start is wired)
- [ ] Win31 appmenu icons (optional external download, not ported); receipts/restore ledger (not built)
- [ ] T2 hardware acceptance (camera, touch bar, Wi-Fi/Bluetooth, suspend/resume) in the Hyprland session

## Added after the first live sessions (2026-11-15)

- [x] Laptop layer (laptop.conf): brightness/keyboard light via logind, volume/mic/media keys with OSD,
      panel off below minimum brightness (backlight 0, no DPMS flash), polkit agent, nm-applet, blueman,
      hypridle, Tailscale tray, Satty screenshots (SUPER+SHIFT+4/S/X)
- [x] Waybar: portals after `uwsm finalize`, compact modules, power-profile drop-down, battery/network
      icons as Material Design glyphs, grey palette, clock right, left reserve strip (config)
- [x] Panel: scale and left reserve from config; whole-pixel border/title bar at fractional scale
- [x] Keyring in Hyprland (ksecretd activation), Chromium/Electron `--password-store=kwallet6` overrides
- [x] High-visibility cursor theme t2-highvis (tools/make_cursor.py), SUPER+SHIFT+C find pointer
- [x] GPU render placement: hypr-gpu battery|external (laptop-gpu-policy research 2026-11-15)
- [x] Sharp X11 apps at fractional scale (2026-11-16): `xwayland:force_zero_scaling`; `hypr-xscale` at
      login sets Xft.dpi = 96 x panel scale, NEdit/x3270 core-font sizes, Xfe `screenres`
- [x] App menu: desktop IDs uwsm refuses (e.g. `Rclone UI.desktop`, space) start from their Exec line
