"""Read-only inspection helpers for the rootless container deploy (tasks/containers.py)."""
import os
import shutil
import subprocess
from pathlib import Path

PACKAGES = (
    "podman", "crun", "passt", "uidmap", "netavark", "aardvark-dns",
    "catatonit", "containers-storage", "podman-compose",
)
DOCKER_SHIM = "podman-docker"
# Installed Docker packages that conflict with podman-docker; never removed by us.
DOCKER_PACKAGES = ("docker.io", "docker-ce", "docker-ce-cli", "docker-cli", "moby-engine", "moby-cli")
SUBID_START = 100000
SUBID_COUNT = 65536

PODMAN_TUI_VERSION = "2.0.0"
PODMAN_TUI_URL = (f"https://github.com/containers/podman-tui/releases/download/v{PODMAN_TUI_VERSION}/"
                  "podman-tui-release-linux_amd64.zip")
PODMAN_TUI_SHA256 = "de1de10344a8ab636c64c2f982bdaa4e05696b642e2dd4692872f56b3254442f"
PODMAN_TUI_MEMBER = f"podman-tui-v{PODMAN_TUI_VERSION}/podman-tui"


def parse_subids(text: str) -> list[tuple[str, int, int]]:
    """Parse /etc/subuid-style text into (owner, start, count); ignore junk lines."""
    entries = []
    for line in text.splitlines():
        parts = line.strip().split(":")
        if len(parts) != 3 or line.lstrip().startswith("#"):
            continue
        try:
            entries.append((parts[0], int(parts[1]), int(parts[2])))
        except ValueError:
            continue
    return entries


def user_has_range(entries, user: str, uid: int, minimum: int = SUBID_COUNT) -> bool:
    return any(owner in (user, str(uid)) and count >= minimum for owner, _, count in entries)


def next_free_start(entries, count: int = SUBID_COUNT) -> int:
    """First start >= SUBID_START that overlaps no existing range (other accounts untouched)."""
    start = SUBID_START
    for _, s, c in sorted(entries, key=lambda e: e[1]):
        if s + c <= start:
            continue
        if s >= start + count:
            break
        start = s + c
    return start


def read_subids(path: str) -> list[tuple[str, int, int]]:
    try:
        return parse_subids(Path(path).read_text())
    except FileNotFoundError:
        return []


def installed(package: str) -> bool:
    result = subprocess.run(["dpkg-query", "-W", "-f=${Status}", package],
                            capture_output=True, text=True, check=False)
    return result.returncode == 0 and result.stdout.strip().endswith(" installed")


def docker_conflicts() -> list[str]:
    """Report foreign Docker installs/commands/env that compatibility setup must not override."""
    found = [f"package {p} installed" for p in DOCKER_PACKAGES if installed(p)]
    docker = shutil.which("docker")
    if docker and not installed(DOCKER_SHIM):
        found.append(f"existing docker command at {docker}")
    for var in ("DOCKER_HOST", "CONTAINER_HOST", "PODMAN_COMPOSE_PROVIDER"):
        if os.environ.get(var):
            found.append(f"environment {var} is set")
    return found


def compose_link_state(path: str = "/usr/local/bin/docker-compose",
                       target: str = "/usr/bin/podman-compose") -> str:
    """'absent', 'owned' (already our link) or 'foreign'."""
    p = Path(path)
    if p.is_symlink() and os.readlink(p) == target:
        return "owned"
    if p.exists() or p.is_symlink():
        return "foreign"
    other = shutil.which("docker-compose")
    if other and Path(other).resolve() != Path(target):
        return "foreign"
    return "absent"
