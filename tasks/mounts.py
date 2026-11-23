"""Network folders at login, from config.toml [[mounts]] (rclone cloud remotes, sshfs SFTP shares).

Run: .venv/bin/pyinfra @local tasks/mounts.py   (user-level, no sudo)

- ~/.local/libexec/t2-mac-kde/t2-mount (+ rclone-offline.py) and the user unit t2-mount@.service,
  wanted by hypr-desktop.target and plasma-workspace.target: every mount comes up in both sessions.
- One ~/.config/t2-mac-kde/mounts/<name>.env per [[mounts]] entry (manage/mounts.py checks the
  config first). A mount taken out of the config is disabled and its settings removed; an active
  mount stays up until logout.
- Logins stay outside the repository: rclone.conf for rclone remotes, ~/.ssh/config + key for sshfs.
- rclone comes from Nix (tasks/nix_tools.py), sshfs from the Ubuntu archive (tasks/apps.py).
"""
import os
from io import StringIO
from pathlib import Path

from pyinfra.operations import files, server

from manage import mounts
from manage.preflight import validate_local_context
from manage.userconfig import setting

validate_local_context()
home = os.path.expanduser("~")
SRC = Path(__file__).resolve().parents[1] / "files/mounts"
libexec = f"{home}/.local/libexec/t2-mac-kde"
env_dir = f"{home}/.config/t2-mac-kde/mounts"
unit_dir = f"{home}/.config/systemd/user"
# Legacy personal setup (~/scripts/mount-<name>.sh + rclone-mount@.service): disabled once the
# same name is managed here, so a mount never starts twice.
LEGACY_UNIT = "rclone-mount@{}.service"

wanted = mounts.entries(setting("mounts"), home)

ops = [files.put(name=f"t2-mount: {f}", src=str(SRC / f), dest=f"{libexec}/{f}", mode="755",
                 create_remote_dir=True) for f in ("t2-mount", "rclone-offline.py")]
unit = files.put(name="User unit t2-mount@.service", src=str(SRC / "t2-mount@.service"),
                 dest=f"{unit_dir}/t2-mount@.service", mode="644", create_remote_dir=True)
files.directory(name="~/.config/t2-mac-kde/mounts", path=env_dir, mode="700")
for m in wanted:
    files.put(name=f"Mount {m['name']}: {m['source']} -> {m['path']}", src=StringIO(mounts.env_file(m)),
              dest=f"{env_dir}/{m['name']}.env", mode="600")
server.shell(name="systemd --user daemon-reload (t2-mount unit changed)", commands=["systemctl --user daemon-reload"],
             _if=unit.did_change)

names = " ".join(m["name"] for m in wanted)
server.shell(
    name=f"Mounts at login (KDE + Hyprland): {names or 'none'}",
    commands=[f"""set -eu
for n in {names}; do
  legacy="{LEGACY_UNIT.format('$n')}"
  if systemctl --user is-enabled -q "$legacy" 2>/dev/null; then
    systemctl --user disable "$legacy"
    echo "$legacy disabled (now t2-mount@$n)"
  fi
  systemctl --user is-enabled -q "t2-mount@$n.service" || systemctl --user enable "t2-mount@$n.service"
  # Starting is harmless while the old unit's mount is up (t2-mount: "already mounted").
  systemctl --user is-active -q "t2-mount@$n.service" || systemctl --user start --no-block "t2-mount@$n.service"
done
# Mounts no longer in the config: disable, drop their settings (an active mount stays until logout).
for f in "{env_dir}"/*.env; do
  [ -e "$f" ] || continue
  n=$(basename "$f" .env)
  case " {names} " in *" $n "*) continue ;; esac
  systemctl --user disable "t2-mount@$n.service" 2>/dev/null || true
  rm -f "$f"
  echo "t2-mount@$n removed (not in config.toml)"
done"""],
)
