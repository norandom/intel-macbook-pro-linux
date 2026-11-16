"""CPU security mitigations on/off (config cpu_mitigations_off, default false).

Owner-approved exception to the protected boot boundary (2026-11-16, see
.kiro/steering/protected-system-boundary.md): a single GRUB drop-in adds `mitigations=off`;
the boot menu is regenerated only when it doesn't match the setting, after a backup of grub.cfg.
Takes effect at the next reboot; new shells remind you until then.

    .venv/bin/pyinfra @local tasks/cpu_mitigations.py --use-sudo-password
"""
import os

from pyinfra import logger
from pyinfra.operations import files, server

from manage import cpu_mitigations as cm
from manage.preflight import validate_local_context
from manage.userconfig import setting

validate_local_context()

off = setting("cpu_mitigations_off", False)
if not isinstance(off, bool):
    raise ValueError("cpu_mitigations_off must be true or false")

if off:
    from io import StringIO
    dropin = files.put(name=f"GRUB drop-in: {cm.OPTION}", src=StringIO(cm.dropin()), dest=cm.DROPIN,
                       mode="644", _sudo=True)
else:
    dropin = files.file(name="GRUB drop-in removed (mitigations on)", path=cm.DROPIN, present=False, _sudo=True)

server.shell(name="Boot menu matches the setting (backup + update-grub only on mismatch)",
             commands=cm.regenerate_commands(), _sudo=True)

files.block(name="New shells: reboot notice while the kernel doesn't match the setting",
            path=os.path.expanduser("~/.bashrc"), marker=cm.NOTICE_MARKER, content=cm.notice(), backup=True)

logger.info(f"cpu mitigations: {'OFF' if off else 'on'} after the next reboot "
            f"(running kernel: {'off' if cm.OPTION in open('/proc/cmdline').read().split() else 'on'})")
