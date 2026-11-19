# Remote access

`tasks/remote_access.py` sets up Tailscale, SSH and fail2ban, plus the firewall rule for RDP.
`tasks/rdp.py` installs the RDP server itself.

## Tailscale

Installed from Tailscale's own apt repo (the signing key is committed and checksummed).
`tailscaled` starts at boot. Log in once:

```sh
sudo tailscale up   # prints a login URL
```

Which exit node you use is your own, private choice, so the repo doesn't configure one: pick it
in the tray or with `tailscale set --exit-node=<name>`. Your desktop user is made the Tailscale operator, so the tray icon can switch exit nodes without
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

## Listener policy

SSH explicitly listens on IPv4 and IPv6 wildcard addresses (port 22), including LAN,
Wi-Fi and Tailscale. Authentication and fail2ban remain enabled. The RDP firewall
continues to accept TCP/UDP 3389 only on loopback and tailscale0. Tailscale prefers
a direct connection, including over the local network; relay fallback is possible,
so a Tailscale address does not guarantee that traffic stays on the LAN.

## Traffic shaping (CAKE)

Off by default. With `cake_upload_mbit` and/or `cake_download_mbit` set, `tasks/traffic_shaping.py`
puts the kernel's CAKE shaper on the Wi-Fi/Ethernet uplinks and on the Tailscale tunnel. The
queue then forms on this machine instead of in the router, connections share the line fairly,
and calls or remote desktop stay responsive while an upload, backup or download fills it.

- Set each rate a little below the measured line speed (about 90-95 %). A rate above what the
  link delivers does nothing, which is also the case on a Wi-Fi link slower than the line.
- With a Tailscale exit node all traffic leaves the uplink as one encrypted flow. The tunnel is
  therefore shaped as well, at 92 % of the rate, so the queue forms where the connections are
  still visible.
- Only this laptop is shaped. Other devices on the same line need shaping on the router
  (OpenWrt: SQM).
- Guests on libvirt's NAT network leave through the same uplinks and are shaped with the host.

```
/usr/local/libexec/t2-cake status    # rates and the active queues (no sudo)
```

Both rates `0` and a re-run remove the unit, the udev rule and the queues; the kernel default
(`fq_codel`) returns. Nothing is written to sysctl, the kernel or the boot configuration.
