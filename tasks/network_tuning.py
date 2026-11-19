"""Sender-side TCP tuning (config network_tuning, default true; owner decision 2026-11-19).

One sysctl.d file: BBR congestion control, no slow start after idle, MTU probing on stalls
(reasons in files/network-tuning/61-t2-network.conf). Runtime sysctls only; no module list,
kernel or boot change. `network_tuning = false` removes the file and puts the kernel
defaults back at once.

    .venv/bin/pyinfra @local tasks/network_tuning.py --use-sudo-password
"""
import os
from pathlib import Path

from pyinfra.operations import files, server

from manage import network_tuning as nt
from manage.preflight import validate_local_context
from manage.userconfig import setting

validate_local_context()
enabled = setting("network_tuning", True)
if not isinstance(enabled, bool):
    raise ValueError("network_tuning must be true or false")

if enabled:
    conf = files.put(name="sysctl: BBR, no slow start after idle, MTU probing",
                     src=str(Path(__file__).resolve().parents[1] / "files/network-tuning/61-t2-network.conf"),
                     dest=nt.DEST, user="root", group="root", mode="644", _sudo=True)
    # Also when the file is unchanged but the running values differ (first boot after a kernel change).
    server.shell(name="Apply only the managed network sysctl file; verify readback",
                 commands=[f"sysctl -p {nt.DEST}", *nt.verify_commands()], _sudo=True,
                 _if=lambda: conf.did_change() or any(
                     open("/proc/sys/" + key.replace(".", "/")).read().split() != [managed]
                     for key, (managed, _default) in nt.SETTINGS.items()))
elif os.path.exists(nt.DEST):
    files.file(name="sysctl: network tuning removed", path=nt.DEST, present=False, _sudo=True)
    server.shell(name="Kernel defaults back (cubic, slow start after idle, no MTU probing)",
                 commands=nt.restore_commands(), _sudo=True)
