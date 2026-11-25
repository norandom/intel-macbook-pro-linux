"""Docker Engine from Docker's apt repo, replacing rootless Podman (owner decision 2026-11-25).

- docker-ce, CLI, containerd, buildx and the compose plugin (`docker compose`, plus a
  `docker-compose` link) in ONE guarded transaction that also removes the Podman packages
  (docker-ce-cli and podman-docker both ship /usr/bin/docker).
- The user joins the docker group (root-equivalent; applies at the next login).
- The daemon is socket-activated: nothing runs until the first docker command (quiet laptop).
- daemon.json: ip-forward-no-drop (Docker would set the FORWARD policy to DROP and cut libvirt's
  VM networks off) and capped json-file logs.
- Leftovers of the Podman setup (our config files, podman-tui, Podman Desktop) are removed.
Image/container data of the old rootless Podman is not touched here (it was reset by hand).
"""
import hashlib
import json
import os
import pwd
from io import StringIO
from pathlib import Path
from shlex import quote

from pyinfra import local, logger
from pyinfra.operations import files, server

from manage import containers as c
from manage.packages import _installed as installed, schedule_batch
from manage.preflight import validate_local_context

validate_local_context()

account = pwd.getpwuid(os.getuid())
user, home = account.pw_name, Path(account.pw_dir)
src = Path(__file__).resolve().parents[1] / "files/containers"


def note(message):
    logger.warning(f"[containers] {message}")


if hashlib.sha256((src / "docker-keyring.gpg").read_bytes()).hexdigest() != c.KEYRING_SHA256:
    raise RuntimeError("Docker archive key does not match the pinned sha256.")

local.include("tasks/package_policy.py")

# --- Docker's apt repo -----------------------------------------------------------------------
files.put(name="Docker archive key", src=str(src / "docker-keyring.gpg"),
          dest="/usr/share/keyrings/docker-archive-keyring.gpg", mode="0644", _sudo=True)
files.put(name="Docker apt source (resolute stable)", src=str(src / "docker.list"),
          dest=f"/etc/apt/sources.list.d/{c.REPO}.list", mode="0644", _sudo=True)

# --- daemon.json (before the install, so the first start already uses it) -------------------
daemon = files.put(name="/etc/docker/daemon.json (no FORWARD DROP for libvirt, capped logs)",
                   src=StringIO(json.dumps(c.DAEMON_CONFIG, indent=2) + "\n"),
                   dest="/etc/docker/daemon.json", mode="0644", create_remote_dir=True, _sudo=True)

# --- Podman out, Docker in: one guarded transaction ------------------------------------------
podman_left = tuple(p for p in c.PODMAN_PACKAGES if installed(p))
docker_missing = [p for p in c.PACKAGES if not installed(p)]
if podman_left:
    # The user socket would dangle once podman is gone.
    server.shell(name="Podman: user socket and service off",
                 commands=["systemctl --user disable --now podman.socket podman.service 2>/dev/null || true"])
if docker_missing or podman_left:
    schedule_batch("Docker Engine", packages=c.PACKAGES, source_lists=(c.REPO,), replaces=podman_left)

# --- Daemon on demand -----------------------------------------------------------------------
server.shell(
    name="Docker: socket-activated (daemon starts with the first docker command)",
    commands=["systemctl is-enabled -q docker.socket || systemctl enable docker.socket",
              "systemctl is-enabled -q docker.service && systemctl disable docker.service containerd.service || true"],
    _sudo=True,
)
server.shell(
    name="Docker: validate daemon.json and restart a running daemon (config changed)",
    commands=["dockerd --validate --config-file /etc/docker/daemon.json",
              "systemctl is-active -q docker.service && systemctl restart docker.service || true"],
    _if=daemon.did_change, _sudo=True,
)
server.shell(
    name=f"{user} in the docker group (root-equivalent; next login)",
    commands=[f"id -nG {quote(user)} | tr ' ' '\\n' | grep -qx docker || usermod -aG docker {quote(user)}"],
    _sudo=True,
)

# --- docker-compose command -----------------------------------------------------------------
if c.compose_link_state() == "foreign":
    note(f"{c.COMPOSE_LINK} exists and is not ours; left unchanged (`docker compose` works).")
else:
    files.link(name="docker-compose -> Docker's compose plugin", path=c.COMPOSE_LINK,
               target=c.COMPOSE_PLUGIN, _sudo=True)

# --- Podman leftovers -----------------------------------------------------------------------
for path in c.PODMAN_SYSTEM_FILES:
    files.file(name=f"Podman setup: remove {path}", path=path, present=False, _sudo=True)
server.shell(
    name="Podman setup: DOCKER_HOST (podman socket) out of the user manager",
    commands=['[ "$(systemctl --user show-environment | sed -n "s/^DOCKER_HOST=//p")" != '
              f'"unix:///run/user/{account.pw_uid}/podman/podman.sock" ] || systemctl --user unset-environment DOCKER_HOST'],
)
opt, bin_dir = home / ".local/opt", home / ".local/bin"
for name in ("podman-tui", "podman-desktop"):
    link = bin_dir / name
    server.shell(
        name=f"Remove our {name} copy",
        commands=[f'if [ -L {quote(str(link))} ]; then case "$(readlink {quote(str(link))})" in '
                  f'{quote(str(opt))}/{name}-*) rm -f {quote(str(link))} ;; esac; fi',
                  f"rm -rf {quote(str(opt))}/{name}-*"],
    )
for path in (home / ".local/share/applications/podman-desktop.desktop",
             home / ".local/share/icons/hicolor/512x512/apps/podman-desktop.png"):
    files.file(name=f"Podman Desktop: remove {path.name}", path=str(path), present=False)
if Path("/etc/apparmor.d/t2-podman-desktop").exists():
    server.shell(name="Podman Desktop: unload and remove its AppArmor profile", _sudo=True, commands=[
        "apparmor_parser -R /etc/apparmor.d/t2-podman-desktop 2>/dev/null || true",
        "rm -f /etc/apparmor.d/t2-podman-desktop"])
