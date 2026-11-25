"""Docker Engine (tasks/containers.py): Docker's own apt repo, replacing rootless Podman.

Owner decision 2026-11-25: Podman goes (packages, images, containers, volumes); Docker Engine
(docker-ce, root daemon, the user in the docker group) takes its place. Not Docker Desktop:
on Linux that runs its own VM with a separate engine.
"""
import os
from pathlib import Path

# download.docker.com/linux/ubuntu/gpg, dearmored. Key 9DC858229FC7DD38854AE2D88D81803C0EBFCD88
# (Docker Release (CE deb)); it verified the resolute InRelease on 2026-11-25.
REPO = "docker"
KEYRING_SHA256 = "a09e26b72228e330d55bf134b8eaca57365ef44bf70b8e27c5f55ea87a8b05e2"
PACKAGES = ("docker-ce", "docker-ce-cli", "containerd.io", "docker-buildx-plugin", "docker-compose-plugin")
# Removed in the same transaction (docker-ce-cli and podman-docker both ship /usr/bin/docker).
# passt and uidmap stay: libvirt and other user-namespace tools use them.
PODMAN_PACKAGES = ("podman", "podman-docker", "podman-compose", "netavark", "aardvark-dns",
                   "catatonit", "containers-storage", "crun")
# Files the Podman setup wrote (all ours); removed once Podman is gone.
PODMAN_SYSTEM_FILES = ("/etc/containers/nodocker",
                       "/etc/containers/registries.conf.d/60-t2-containers.conf",
                       "/etc/containers/containers.conf.d/60-t2-containers.conf")
# /etc/docker/daemon.json. ip-forward-no-drop (Docker 28+): enabling forwarding no longer sets the
# iptables FORWARD policy to DROP, which cuts libvirt's NAT networks off. Logs: json-file rotated.
DAEMON_CONFIG = {
    "ip-forward-no-drop": True,
    "log-driver": "json-file",
    "log-opts": {"max-size": "10m", "max-file": "3"},
}
COMPOSE_LINK = "/usr/local/bin/docker-compose"
COMPOSE_PLUGIN = "/usr/libexec/docker/cli-plugins/docker-compose"
OLD_COMPOSE_TARGET = "/usr/bin/podman-compose"


def compose_link_state(path: str = COMPOSE_LINK) -> str:
    """'absent', 'ours' (our old podman-compose link or the new plugin link) or 'foreign'."""
    p = Path(path)
    if p.is_symlink() and os.readlink(p) in (OLD_COMPOSE_TARGET, COMPOSE_PLUGIN):
        return "ours"
    if p.exists() or p.is_symlink():
        return "foreign"
    return "absent"
