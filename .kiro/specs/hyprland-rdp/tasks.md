# Implementation (practical port, upstream release)

Entry: `.venv/bin/pyinfra @local tasks/rdp.py [--data rdp_bind=0.0.0.0:3389] [--data rdp_audio_mode=off]`
Starts with the Hyprland session (hypr-desktop.target wants it); off in KDE. Manual: `hypr-rdp-control start|stop|status`

## Done
- [x] Upstream MuNeNiCK/hypr-rdp v0.1.8 archive pinned (URL, size 8936327, sha256 f8b324fc...); no fork, patches or build
- [x] Archive downloaded in isolation and checked: plain members only, x86-64 ELF, interp /lib64/ld-linux-x86-64.so.2,
      max GLIBC_2.39; every NEEDED lib resolves on this Ubuntu 26.04 host (ldconfig, no ldd, never executed)
- [x] Executable sha256 064eace8... pinned too; install re-verifies archive size+sha, member type and binary sha
- [x] Installed user-level to ~/.local/opt/hypr-rdp/v0.1.8 (+ `current` link); no sudo, no /usr/local/bin shadowing
- [x] Runtime libs via install_packages (libgbm1 libpam0g libxkbcommon0 libva2 libva-drm2 libpipewire-0.3-0t64
      libstdc++6 zlib1g curl ca-certificates); no PAM config, no audio-stack change
- [x] Config ~/.config/t2-mac-kde/rdp/config.toml (0600): auth_mode=configured, username, generated 0600 password_file,
      no inline password, keyboard_layout_policy=compositor, audio_mode=mirror (or off; redirect rejected),
      file_transfer_mode=off, capture wlr / avc420 / h264 auto, no software-rendering env
- [x] Bind defaults to 127.0.0.1:3389; LAN exposure only via explicit `rdp_bind`; no firewall changes
- [x] Upstream session hooks -> fixed `~/.local/bin/hypr-rdp-session` (log + private runtime state only); source
      journal watcher, mode cache, console blanking, input disabling, cursor hiding, unlock-on-connect dropped
- [x] `t2-hypr-rdp.service`: WantedBy/PartOf/Requisite=hypr-desktop.target (desktop starts it via Hyprland exec-once),
      ConditionEnvironment=HYPRLAND_INSTANCE_SIGNATURE (never in KDE), stops with the session; `run` waits up to 15 s for
      a ready session; bounded restart, no loop on invalid config/session/gate (exit 1/2)
- [x] `hypr-rdp-control validate|start|stop|status|mark-verified|run`: requires explicit HYPRLAND_INSTANCE_SIGNATURE,
      consumes `hypr-session status --json` schema 1 (uid/instance/ready), falls back to own live IPC socket check
- [x] Compatibility gate: non-loopback bind refused until `mark-verified` records binary sha + compositor version
- [x] Deploy never restarts a running server (daemon-reload only; reconnect/restart applies config)
- [x] tests/test_rdp.py: config rejection, secret redaction, session selection, gate invalidation, unit/hook scope

## Deferred / needs live owner check
- [ ] Native Hyprland 0.53.3 runtime compatibility (upstream declares 0.54+): test over loopback/SSH tunnel, then mark-verified
- [ ] TLS: upstream self-signed cert generated on first start; client must verify fingerprint on first connect
- [ ] Auth rejection, reconnect/replacement, resize, lock preserved, local outputs/input intact after disconnect (live client)
- [ ] Mirror audio keeps T2 speakers/mic routing (live); Option+L=@, de/us, Super over RDP (live client)
- [ ] Clipboard text/image (live); file transfer stays off until FUSE + client direction tests pass
- [ ] `hypr-desktop.target` unit file must ship from the hyprland-desktop spec; the wants link is inert until then
- [ ] fail2ban not shipped: v0.1.8 never logs the client IP on auth failure at its default log level (see report)
- [ ] No headless/boot-time session (owner decision): hypr-rdp needs a running Hyprland; nothing at the SDDM greeter
- [ ] P23 assembled checklist tool (tools/validate_assembled_port.py): not implemented; ceremony deferred per execution policy
- [ ] Ownership receipts / restore: not implemented (plain managed files; password file never overwritten)
