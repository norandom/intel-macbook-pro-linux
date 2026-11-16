"""T2 pack and update policy: hold the tested package versions (config t2_pack_pin, default false) and back up
their .debs to ~/.local/share/t2-mac-kde/t2-packs/<id> (config t2_pack_backup, default true);
config background_updates = false stops apt's background refresh and unattended upgrades.

Owner-approved exception to the protected boundary (2026-11-16, see
.kiro/steering/protected-system-boundary.md): one apt preferences file, nothing installed,
upgraded or removed. Moving to a new pack is an owner-run apt step (docs/t2-pack.md).

    .venv/bin/pyinfra @local tasks/t2_pack.py --use-sudo-password
"""
import shlex
from io import StringIO
from pathlib import Path

from pyinfra import logger
from pyinfra.operations import files, server

from manage import t2_pack
from manage.preflight import validate_local_context
from manage.userconfig import setting

validate_local_context()

pack = t2_pack.load()
pin = setting("t2_pack_pin", False)
keep_debs = setting("t2_pack_backup", True)
for key, value in (("t2_pack_pin", pin), ("t2_pack_backup", keep_debs)):
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be true or false")

if pin:
    files.put(name=f"apt pin: T2 pack {pack['id']} ({len(pack['packages'])} packages at priority {t2_pack.PRIORITY})",
              src=StringIO(t2_pack.pref(pack)), dest=t2_pack.PREF, mode="644", _sudo=True)
else:
    files.file(name="apt pin: T2 pack removed (t2_pack_pin = false)", path=t2_pack.PREF, present=False, _sudo=True)

# Background apt (config background_updates, default true = Ubuntu's behaviour). false: the
# periodic apt jobs, unattended-upgrades and the update notifier stop; nothing else changes.
background = setting("background_updates", True)
if not isinstance(background, bool):
    raise ValueError("background_updates must be true or false")
timers = " ".join(t2_pack.NO_BG_TIMERS)
if not background:
    files.put(name="apt: no background updates (config background_updates = false)",
              src=StringIO(t2_pack.no_background_conf()), dest=t2_pack.NO_BG_CONF, mode="644", _sudo=True)
    server.shell(name="Background apt timers off (apt-daily, unattended-upgrades, update notifier)",
                 commands=[f"systemctl disable --now {timers}"], _sudo=True)
elif Path(t2_pack.NO_BG_CONF).exists():
    # Only undo what this task did: re-enable the timers it disabled.
    files.file(name="apt: background updates back on", path=t2_pack.NO_BG_CONF, present=False, _sudo=True)
    server.shell(name="Background apt timers on again", commands=[f"systemctl enable --now {timers}"], _sudo=True)

if keep_debs:
    root = Path(__file__).resolve().parents[1]
    server.shell(
        name=f".deb backup of T2 pack {pack['id']} -> {t2_pack.BACKUP_ROOT / pack['id']} (sha256 vs packs/)",
        commands=[f"cd {shlex.quote(str(root))} && .venv/bin/python tools/t2-pack backup"],
    )

drift = [r for r in t2_pack.status(pack) if r["installed"] and r["installed"] != r["pack"]]
for r in drift:
    logger.warning(f"t2 pack {pack['id']}: {r['package']} installed {r['installed']}, pack says {r['pack']}")
