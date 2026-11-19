"""CAKE traffic shaper (config cake_upload_mbit / cake_download_mbit, default 0 = off).

Keeps the queue on this machine instead of in the router: calls and remote desktop stay
responsive while uploads, backups or downloads fill the line. Set each rate a little below
the measured line speed (about 90-95 %). Shapes the physical uplinks and, slightly lower,
the Tailscale tunnel (see files/traffic-shaping/t2-cake). Runtime only: qdiscs, one oneshot
unit and one udev rule; no sysctl, kernel or boot change. Both rates 0 removes everything.

    .venv/bin/pyinfra @local tasks/traffic_shaping.py --use-sudo-password
    /usr/local/libexec/t2-cake status
"""
import os
from io import StringIO
from pathlib import Path

from pyinfra.operations import files, server, systemd

from manage import traffic_shaping as ts
from manage.preflight import validate_local_context
from manage.userconfig import setting

validate_local_context()
up = ts.kbit(setting("cake_upload_mbit", 0), "cake_upload_mbit")
down = ts.kbit(setting("cake_download_mbit", 0), "cake_download_mbit")
src = Path(__file__).resolve().parents[1] / "files/traffic-shaping"

if up or down:
    files.directory(name="Helper directory", path="/usr/local/libexec", user="root", group="root", mode="755", _sudo=True)
    changed = [
        files.put(name="CAKE helper: t2-cake", src=str(src / "t2-cake"), dest=ts.HELPER,
                  user="root", group="root", mode="755", _sudo=True),
        files.put(name=f"CAKE rates: up {up} kbit/s, down {down} kbit/s", src=StringIO(ts.conf(up, down)), dest=ts.CONF,
                  user="root", group="root", mode="644", create_remote_dir=True, _sudo=True),
        files.put(name="CAKE unit: t2-cake.service", src=str(src / "t2-cake.service"), dest=ts.UNIT,
                  user="root", group="root", mode="644", _sudo=True),
    ]
    rule = files.put(name="CAKE udev rule: shape interfaces that appear later", src=str(src / "90-t2-cake.rules"),
                     dest=ts.RULE, user="root", group="root", mode="644", _sudo=True)
    systemd.daemon_reload(name="Reload unit definitions (CAKE)", _if=changed[2].did_change, _sudo=True)
    server.shell(name="Reload udev rules (CAKE)", commands=["udevadm control --reload"], _if=rule.did_change, _sudo=True)
    systemd.service(name="CAKE shaper on, also at boot", service="t2-cake.service", running=True, enabled=True, _sudo=True)
    systemd.service(name="Re-apply CAKE after changes", service="t2-cake.service", restarted=True,
                    _if=lambda: any(op.did_change() for op in changed), _sudo=True)
elif os.path.exists(ts.UNIT):
    # Stopping the unit runs `t2-cake clear`: the kernel's default queue (fq_codel) returns.
    systemd.service(name="CAKE shaper off", service="t2-cake.service", running=False, enabled=False, _sudo=True)
    for path in (ts.RULE, ts.UNIT, ts.CONF, ts.HELPER):
        files.file(name=f"Remove {path}", path=path, present=False, _sudo=True)
    systemd.daemon_reload(name="Reload unit definitions (CAKE removed)", _sudo=True)
    server.shell(name="Reload udev rules (CAKE removed)", commands=["udevadm control --reload"], _sudo=True)
