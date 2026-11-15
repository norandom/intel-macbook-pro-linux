"""Rootless, daemonless Podman with docker / docker compose / docker-compose aliases and podman-tui.

Ported from the worker VM's tasks/containers.py. Local differences: existing Docker installs,
docker-compose commands and user registry policy are detected and preserved (reported, not
replaced); the source CPUWeight=200 for containers is NOT applied (laptop desktop responsiveness);
podman-tui (not packaged in Ubuntu) comes from the pinned, sha256-checked upstream release into ~/.local.
"""
import os
import pwd
from io import StringIO
from pathlib import Path
from shlex import quote

from pyinfra import local, logger
from pyinfra.operations import files, server

from manage import containers as c
from manage.packages import PackageRequest, install_packages
from manage.preflight import validate_local_context

validate_local_context()

account = pwd.getpwuid(os.getuid())
user, uid, home = account.pw_name, account.pw_uid, Path(account.pw_dir)
MARK = "# Managed by t2-mac-kde (rootless-containers)\n"


def note(message):
    logger.warning(f"[containers] {message}")


# --- Packages -------------------------------------------------------------------------------
conflicts = c.docker_conflicts()
packages = c.PACKAGES
if conflicts:
    note("Docker compatibility shim skipped, existing Docker preserved: " + "; ".join(conflicts))
else:
    packages += (c.DOCKER_SHIM,)

local.include("tasks/package_policy.py")
install_packages(PackageRequest(packages=packages, source="ubuntu"))

# --- Subordinate IDs (keep valid existing ranges; append only when absent) --------------------
for kind, db in (("uids", "/etc/subuid"), ("gids", "/etc/subgid")):
    entries = c.read_subids(db)
    if c.user_has_range(entries, user, uid):
        continue
    if any(owner in (user, str(uid)) for owner, _, _ in entries):
        raise RuntimeError(f"{db} has a range for {user} smaller than {c.SUBID_COUNT}; "
                           "enlarging it would remap container data. Fix manually.")
    start = c.next_free_start(entries)
    server.shell(
        name=f"Allocate subordinate {kind} {start}-{start + c.SUBID_COUNT - 1} for {user}",
        commands=[f"usermod --add-sub{kind} {start}-{start + c.SUBID_COUNT - 1} {quote(user)}"],
        _sudo=True,
    )

# --- System configuration (source behavior) --------------------------------------------------
if not Path("/etc/containers/nodocker").exists():
    files.put(name="Silence podman-docker's 'emulate Docker CLI' notice",
              src=StringIO(""), dest="/etc/containers/nodocker", mode="644", _sudo=True)

user_registries = home / ".config/containers/registries.conf"
if user_registries.exists() or os.environ.get("CONTAINERS_REGISTRIES_CONF"):
    note(f"Short-name policy not applied: user registry policy present ({user_registries} or "
         "CONTAINERS_REGISTRIES_CONF) and is preserved.")
else:
    files.put(
        name="Short image names resolve to docker.io (like Docker)",
        src=StringIO(MARK + 'unqualified-search-registries = ["docker.io"]\nshort-name-mode = "permissive"\n'),
        dest="/etc/containers/registries.conf.d/60-t2-containers.conf",
        mode="644",
        create_remote_dir=True,
        _sudo=True,
    )

files.put(
    name="`docker compose` / `podman compose` use podman-compose (no daemon, no socket)",
    src=StringIO(MARK + '[engine]\ncompose_providers = ["/usr/bin/podman-compose"]\ncompose_warning_logs = false\n'),
    dest="/etc/containers/containers.conf.d/60-t2-containers.conf",
    mode="644",
    create_remote_dir=True,
    _sudo=True,
)

link_state = c.compose_link_state()
if link_state == "foreign":
    note("docker-compose link skipped: an existing docker-compose command is preserved.")
else:
    files.link(name="docker-compose -> podman-compose", path="/usr/local/bin/docker-compose",
               target="/usr/bin/podman-compose", _sudo=True)

# --- User lifecycle ---------------------------------------------------------------------------
if Path(f"/var/lib/systemd/linger/{user}").exists():
    note(f"Linger already enabled for {user}.")
else:
    server.shell(name=f"Linger for {user}: containers run independent of the login session",
                 commands=[f"loginctl enable-linger {quote(user)}"], _sudo=True)

# podman-tui talks to the API socket; socket-activated, user-only ($XDG_RUNTIME_DIR/podman/podman.sock).
server.shell(
    name="podman.socket (user, for podman-tui)",
    commands=["systemctl --user is-enabled -q podman.socket || systemctl --user enable --now podman.socket"],
)

note("Source CPUWeight=200 for container slice not applied on this laptop (current scheduling retained).")

# --- podman-tui (not in Ubuntu archive): pinned upstream release, sha256-verified ----------------
opt = home / ".local/opt" / f"podman-tui-{c.PODMAN_TUI_VERSION}"
binary, bin_link = opt / "podman-tui", home / ".local/bin/podman-tui"
if bin_link.exists() and not bin_link.is_symlink():
    note(f"podman-tui not installed: foreign {bin_link} is preserved.")
else:
    if not binary.is_file():
        server.shell(
            name=f"Install podman-tui v{c.PODMAN_TUI_VERSION} to {opt}",
            commands=[f"""set -eu
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
curl -fsSL --proto '=https' -o "$t/a.zip" {quote(c.PODMAN_TUI_URL)}
echo "{c.PODMAN_TUI_SHA256}  $t/a.zip" | sha256sum -c --quiet -
python3 -I -c 'import sys,zipfile; zipfile.ZipFile(sys.argv[1]).extract(sys.argv[2], sys.argv[3])' "$t/a.zip" {quote(c.PODMAN_TUI_MEMBER)} "$t/x"
chmod 755 "$t/x/{c.PODMAN_TUI_MEMBER}"
"$t/x/{c.PODMAN_TUI_MEMBER}" version | grep -q {quote(c.PODMAN_TUI_VERSION)}
mkdir -p {quote(str(opt))}
install -m 755 "$t/x/{c.PODMAN_TUI_MEMBER}" {quote(str(binary))}
"""],
        )
    files.link(name="~/.local/bin/podman-tui", path=str(bin_link), target=str(binary),
               create_remote_dir=True)
