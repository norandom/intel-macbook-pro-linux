"""Nix for user CLI tools (spec nix-user-tools).

Run: .venv/bin/pyinfra @local tasks/nix_tools.py [--dry]

- Ubuntu's nix-setup-systemd (+ nix-bin) through the package guard; nix-daemon.socket enabled;
  the desktop user joins nix-users (the daemon socket is root:nix-users 0770).
- ~/.config/nix/nix.conf enables flakes and the nix command for the user only.
- nix/flake.nix (+ committed flake.lock) and tools.json from config nix_tools are copied to
  ~/.local/share/t2-mac-kde/nix/; the "t2-tools" profile entry is installed or upgraded from there
  when those inputs change (stamp ~/.local/state/t2-mac-kde/nix-tools.sha).
- ~/.nix-profile/bin first in PATH (~/.bashrc block; uwsm env-hyprland in tasks/desktop.py).
- Release binaries we installed for tools Nix now provides are removed once Nix has them.
- Weekly GC user timer (nix-gc.timer).
"""
import os
import pwd
import shutil
from io import StringIO
from pathlib import Path
from shlex import quote

from pyinfra import host, logger
from pyinfra.facts.server import Command
from pyinfra.operations import files, server, systemd

from manage import nix_tools as nt
from manage.applications import RELEASE_FALLBACK
from manage.packages import PackageRequest, install_packages
from manage.preflight import validate_local_context
from manage.userconfig import setting

validate_local_context()

repo = Path(__file__).resolve().parent.parent
user = pwd.getpwuid(os.getuid()).pw_name
home = Path(pwd.getpwuid(os.getuid()).pw_dir)
flake_dir = home / ".local/share/t2-mac-kde/nix"
stamp_file = home / ".local/state/t2-mac-kde/nix-tools.sha"
bin_dir = home / ".local/bin"
units = home / ".config/systemd/user"
# nix_tools replaces the default list; nix_tools_extra adds to it (the usual way to add a tool)
selected = nt.tools(list(nt.tools(setting("nix_tools"))) + list(setting("nix_tools_extra", [])))


def holds(check):
    """True when `check` succeeds; evaluated at execution time (after earlier ops)."""
    return lambda: host.get_fact(
        Command, command="bash -c " + quote(f"({check}) >/dev/null 2>&1 && echo yes || echo no")) == "yes"


# --- Nix from the Ubuntu archive (multi-user daemon, package-owned units) ------------------
install_packages(PackageRequest(packages=("nix-setup-systemd",), source="ubuntu"))
server.shell(
    name="nix-daemon.socket enabled and listening",
    # The package's postinst may start nix-daemon.service directly; systemd then refuses the
    # socket ("Socket service nix-daemon.service already active"). Stop it, start the socket;
    # the socket activates the daemon on the next use.
    commands=["systemctl enable nix-daemon.socket",
              "systemctl is-active -q nix-daemon.socket || { systemctl stop nix-daemon.service; "
              "systemctl start nix-daemon.socket; }",
              "systemctl is-active -q nix-daemon.socket"], _sudo=True,
    _if=lambda: not holds("systemctl is-enabled -q nix-daemon.socket && systemctl is-active -q nix-daemon.socket")(),
)
server.shell(
    name=f"{user} in group nix-users (daemon socket access; new logins get it, deploy uses sg)",
    commands=[f"usermod -aG nix-users {quote(user)}"], _sudo=True,
    _if=lambda: holds("getent group nix-users")()
    and not holds(f"id -nG {quote(user)} | tr ' ' '\\n' | grep -qx nix-users")(),
)
files.put(name="~/.config/nix/nix.conf: flakes + nix command (user only)",
          src=StringIO("# Managed by t2-mac-kde (nix-user-tools)\nexperimental-features = nix-command flakes\n"),
          dest=str(home / ".config/nix/nix.conf"), mode="644", create_remote_dir=True)

# --- Flake inputs in the user dir (the repo tree never holds config-dependent files) -------
flake = (repo / "nix/flake.nix").read_bytes()
repo_lock = repo / "nix/flake.lock"
tools_text = nt.tools_json(selected).encode()
files.put(name="Nix flake: flake.nix -> ~/.local/share/t2-mac-kde/nix/", src=str(repo / "nix/flake.nix"),
          dest=str(flake_dir / "flake.nix"), mode="644", create_remote_dir=True)
files.put(name=f"Nix flake: tools.json ({len(selected)} tools, config nix_tools)", src=StringIO(tools_text.decode()),
          dest=str(flake_dir / "tools.json"), mode="644", create_remote_dir=True)
if repo_lock.is_file():
    lock = repo_lock.read_bytes()
    files.put(name="Nix flake: flake.lock (repo pin)", src=str(repo_lock),
              dest=str(flake_dir / "flake.lock"), mode="644", create_remote_dir=True)
else:
    user_lock = flake_dir / "flake.lock"
    lock = user_lock.read_bytes() if user_lock.is_file() else b""
    logger.info(f"nix_tools: nix/flake.lock is not in the repo yet. After the first profile install run: "
                f"cp {user_lock} {repo}/nix/ && git -C {repo} add nix/flake.lock && git commit")
expected = nt.stamp(flake, lock, tools_text)

script = (repo / "files/nix/t2-nix-update").read_text().replace("@REPO@", quote(str(repo)))
files.put(name="~/.local/bin/t2-nix-update (flake update + profile upgrade + lock back to repo)",
          src=StringIO(script), dest=str(bin_dir / "t2-nix-update"), mode="755", create_remote_dir=True)


def profile_outdated():
    if not shutil.which("nix"):  # dry run before the apt install, or install failed
        return False
    try:
        return stamp_file.read_text().strip() != expected
    except FileNotFoundError:
        return True


server.shell(
    name=f"Nix profile t2-tools: install/upgrade ({', '.join(selected) or 'empty'})",
    commands=[f"{quote(str(bin_dir / 't2-nix-update'))} --apply"],
    _shell_executable="bash",
    _if=profile_outdated,
)

# --- Release binaries we installed for tools Nix now provides (only ours, only once Nix has them)
nix_bin = home / ".nix-profile/bin"
marks = home / ".local/share/t2-mac-kde/release-tools"
for app_id, attr in nt.MIGRATED.items():
    if attr not in selected:
        continue
    if app_id == "podman-tui":  # tasks/containers.py: ~/.local/bin link into ~/.local/opt/podman-tui-*
        link, opt = bin_dir / "podman-tui", home / ".local/opt"
        server.shell(
            name="Remove our podman-tui release copy (Nix provides it)",
            commands=[f'rm -f {quote(str(link))} && rm -rf {quote(str(opt))}/podman-tui-*'],
            _if=holds(f'[ -x {quote(str(nix_bin / "podman-tui"))} ] && [ -L {quote(str(link))} ] && '
                      f'case "$(readlink {quote(str(link))})" in {quote(str(opt))}/podman-tui-*) true ;; *) false ;; esac'),
        )
        continue
    if app_id not in RELEASE_FALLBACK:
        continue
    dest, mark = bin_dir / app_id, marks / f"{app_id}.sha256"
    server.shell(
        name=f"Remove our {app_id} release binary from ~/.local/bin (Nix provides it)",
        commands=[f"rm -f {quote(str(dest))} {quote(str(mark))}"],
        _if=holds(f"[ -x {quote(str(nix_bin / app_id))} ] && [ -f {quote(str(mark))} ]"),
    )

# --- PATH: Nix profile first (before the ble.sh attach block, after ~/.local/bin) -----------
files.block(
    name="bash: ~/.nix-profile/bin first in PATH",
    path=str(home / ".bashrc"), marker=nt.PATH_MARKER, content=nt.PATH_BLOCK,
    before=True, line=nt.BLESH_ATTACH_LINE, try_prevent_shell_expansion=True, backup=True,
)

# --- Weekly garbage collection (user timer; independent of the Hyprland session) ------------
gc_ops = [files.put(name=f"Nix GC unit: {unit}", src=StringIO("# Managed by t2-mac-kde (nix-user-tools)\n" + body),
                    dest=str(units / unit), mode="644", create_remote_dir=True)
          for unit, body in nt.GC_UNITS.items()]
server.shell(name="systemd user daemon-reload (nix-gc units)", commands=["systemctl --user daemon-reload"],
             _if=lambda: any(op.did_change() for op in gc_ops))
systemd.service(name="nix-gc.timer (weekly, keep 30 days)", service="nix-gc.timer", user_mode=True,
                enabled=True, running=True)
