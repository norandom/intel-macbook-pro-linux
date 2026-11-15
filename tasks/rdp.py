"""hypr-rdp (upstream MuNeNiCK release, unmodified) for the T2 Hyprland session.

Port of the source tasks/hypr_rdp.py without the fork .deb, source build, patches,
journal watcher, mode cache, console blanking, input disabling or unlock-on-connect.
Everything is user-level except the runtime library packages. The unit is installed
and wanted by hypr-desktop.target, so it starts and stops with the Hyprland session
(never in KDE). Manual control: `hypr-rdp-control start|stop|status`.

    .venv/bin/pyinfra @local tasks/rdp.py --dry
    .venv/bin/pyinfra @local tasks/rdp.py --data rdp_bind=127.0.0.1:3389   # loopback only
"""
import os
import pwd
from pathlib import Path
from shlex import quote

from pyinfra import host
from pyinfra.facts.server import Command
from pyinfra.operations import files, server
from manage.packages import PackageRequest, install_packages
from manage.preflight import validate_local_context

validate_local_context()

VERSION = "v0.1.8"
URL = f"https://github.com/MuNeNiCK/hypr-rdp/releases/download/{VERSION}/hypr-rdp-{VERSION}-x86_64-linux.tar.gz"
ARCHIVE_SHA256 = "f8b324fcf5c169dd4df269685294db55078b4d6a28cd47a6a86e00d35671b0fd"
ARCHIVE_SIZE = 8936327
# sha256 of the hypr-rdp executable inside that archive (readelf-inspected, never run):
# x86-64 ELF, interpreter /lib64/ld-linux-x86-64.so.2, max GLIBC_2.39, NEEDED below.
BINARY_SHA256 = "064eace8b03f213b5589143d42805be9b01a6fd3319f62b43adde2929ef83713"

user = pwd.getpwuid(os.getuid()).pw_name
home = Path(pwd.getpwuid(os.getuid()).pw_dir)
if Path.home() != home:
    raise RuntimeError("HOME must match the local desktop account before provisioning hypr-rdp.")

# All interfaces, but tasks/remote_access.py firewalls 3389 to tailscale0/lo only.
bind = str(host.data.get("rdp_bind") or "0.0.0.0:3389")
audio_mode = str(host.data.get("rdp_audio_mode") or "mirror")
if audio_mode not in ("mirror", "off"):
    raise RuntimeError("rdp_audio_mode must be mirror or off; redirect would move local audio.")

opt = home / ".local/opt/hypr-rdp"
dest = opt / VERSION
cfg_dir = home / ".config/t2-mac-kde/rdp"
password_file = cfg_dir / "password"
bin_dir = home / ".local/bin"
unit_dir = home / ".config/systemd/user"
repo = Path(__file__).resolve().parent.parent

# libgbm.so.1 libpam.so.0 libxkbcommon.so.0 libva(-drm).so.2 libpipewire-0.3.so.0
# libstdc++/libgcc_s/libz/libc: library packages only; no PAM config, no audio stack change.
install_packages(PackageRequest(
    packages=("curl", "ca-certificates", "libgbm1", "libpam0g", "libxkbcommon0", "libva2",
              "libva-drm2", "libpipewire-0.3-0t64", "libstdc++6", "zlib1g"),
    source="ubuntu",
))

def binary_missing():
    check = f"echo '{BINARY_SHA256}  {dest}/hypr-rdp' | sha256sum -c --status && echo yes || echo no"
    return host.get_fact(Command, command=f"bash -c {quote(check)}") != "yes"

server.shell(
    name=f"hypr-rdp {VERSION} from the upstream release (pinned sha256, no build)",
    commands=f"""set -euo pipefail
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
curl -fsSL --proto '=https' -o "$tmp/a.tgz" {quote(URL)}
[ "$(stat -c %s "$tmp/a.tgz")" = {ARCHIVE_SIZE} ]
echo '{ARCHIVE_SHA256}  '"$tmp/a.tgz" | sha256sum -c --quiet
# the member must be a plain file named hypr-rdp (no links, no paths)
tar tvzf "$tmp/a.tgz" hypr-rdp | grep -q '^-rwx'
mkdir "$tmp/x"
tar xzf "$tmp/a.tgz" -C "$tmp/x" --no-same-owner --no-same-permissions hypr-rdp LICENSE
echo '{BINARY_SHA256}  '"$tmp/x/hypr-rdp" | sha256sum -c --quiet
mkdir -p {quote(str(dest))}
install -m 755 "$tmp/x/hypr-rdp" {quote(str(dest))}/hypr-rdp
install -m 644 "$tmp/x/LICENSE" {quote(str(dest))}/LICENSE
""",
    _shell_executable="bash",
    _if=binary_missing,
)
files.link(name="hypr-rdp current version", path=str(opt / "current"), target=VERSION, symbolic=True)

files.directory(name="RDP config directory", path=str(cfg_dir), mode="700")
server.shell(
    name="RDP password (generated once, owner-only, never in the repo)",
    commands=f"[ -s {quote(str(password_file))} ] || "
             f"(umask 077; head -c 18 /dev/urandom | base64 | tr -d '/+=' > {quote(str(password_file))})",
)
files.template(
    name="hypr-rdp config (auth configured, mirror audio, compositor keymap)",
    src=str(repo / "templates/rdp/config.toml.j2"),
    dest=str(cfg_dir / "config.toml"),
    mode="600",
    rdp_version=VERSION, bind=bind, rdp_user=user, password_file=str(password_file), fps=int(host.data.get("rdp_fps") or 20), egfx_codec=str(host.data.get("rdp_egfx_codec") or "clearcodec"),
    audio_mode=audio_mode, hook=str(bin_dir / "hypr-rdp-session"),
)
for name in ("hypr-rdp-control", "hypr-rdp-session"):
    files.put(name=f"Helper: {name}", src=str(repo / "files/rdp" / name), dest=str(bin_dir / name), mode="755")

unit = files.put(
    name="User unit: t2-hypr-rdp.service",
    src=str(repo / "files/rdp/t2-hypr-rdp.service"),
    dest=str(unit_dir / "t2-hypr-rdp.service"),
    mode="644",
)
# Enabled into hypr-desktop.target (desktop spec; started by Hyprland exec-once only, never
# in KDE). The link is harmless while that target does not exist yet.
files.link(
    name="Start hypr-rdp with the Hyprland session (hypr-desktop.target.wants)",
    path=str(unit_dir / "hypr-desktop.target.wants/t2-hypr-rdp.service"),
    target=str(unit_dir / "t2-hypr-rdp.service"),
)
# No restart: a running server keeps its config until the owner reconnects/restarts it.
server.shell(
    name="Reload user units (no restart; reconnect to apply config changes)",
    commands="systemctl --user daemon-reload 2>/dev/null || true",
    _if=unit.did_change,
)
