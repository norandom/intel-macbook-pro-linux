# Remote access

`tasks/remote_access.py` sets up Tailscale, SSH and fail2ban, plus the firewall rule for RDP.
`tasks/rdp.py` installs the RDP server itself.

## Tailscale

Installed from Tailscale's own apt repo (the signing key is committed and checksummed).
`tailscaled` starts at boot. Log in once:

```sh
sudo tailscale up   # prints a login URL
```

Your desktop user is made the Tailscale operator, so the tray icon can switch exit nodes without
sudo. The tray (`tailscale systray`) runs in the Hyprland session. With an exit node on, the LAN
(printers, NAS, the VM host side) stays reachable.

## SSH

- `sshd` runs as a normal service from boot (socket activation is off).
- A drop-in (`/etc/ssh/sshd_config.d/10-t2-mac-kde.conf`) sets `PermitRootLogin no` and
  `MaxAuthTries 4`.
- Password login stays on until `~/.ssh/authorized_keys` exists. Add a key and re-run the task
  to switch to key-only.

## fail2ban

An sshd jail with a 1 hour ban after 5 failures in 10 minutes. Loopback and Tailscale addresses
(100.64.0.0/10) are never banned; they're already authenticated by Tailscale.

## RDP into the Hyprland session

[hypr-rdp](https://github.com/MuNeNiCK/hypr-rdp) (pinned release, checksummed, unmodified) shares
the running Hyprland session. It starts and stops with that session, never in KDE.

- Port 3389 only accepts connections on `tailscale0` and loopback (an nftables table,
  `t2-rdp-firewall.service`). Peers on the same LAN still connect directly through Tailscale, so
  local use stays fast.
- User name: your login name. Password: generated once into
  `~/.config/t2-mac-kde/rdp/password` (owner-only, never in the repo).
- Lossless ClearCodec at 20 fps by default, sharp enough for terminals and dashboards all day.
  `rdp_egfx_codec = "avc420"` switches to H.264.
- Audio is mirrored: the laptop speakers keep playing. Redirecting audio isn't allowed, because
  it would move the default output.
- The keyboard follows the compositor, so Option+L = @, layout switching and SUPER shortcuts work
  as they do locally.
- File transfer over the clipboard is off.

Connect with any RDP client to the Mac's Tailscale name or IP on port 3389.

```sh
hypr-rdp-control status     # service state and the last session event
hypr-rdp-control validate   # check config, password file and session
hypr-rdp-control start      # or stop
```

Upstream declares Hyprland 0.54+, and Ubuntu ships 0.53. The default capture mode works on 0.53;
the server starts with a warning until you run `hypr-rdp-control mark-verified` for that binary
and compositor version.

## Change it

| You want | Change |
|---|---|
| RDP on loopback only | `rdp_bind = "127.0.0.1:3389"` |
| H.264, another frame rate, no audio | `rdp_egfx_codec`, `rdp_fps`, `rdp_audio_mode = "off"` |
| Other fail2ban limits | `files/remote-access/fail2ban-t2.conf` |
| No RDP at all | remove `"rdp"` from `deploy.py` |

`~/.config/t2-mac-kde/rdp/config.toml` is rewritten on every run of `tasks/rdp.py`; change the
template `templates/rdp/config.toml.j2` or the config keys instead. A running server keeps its
settings until you restart it.

Re-run: `.venv/bin/pyinfra @local tasks/remote_access.py --use-sudo-password` or `tasks/rdp.py`.
