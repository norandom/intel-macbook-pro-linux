"""Default earlier cooling; runtime sysfs only, no driver reload or boot changes."""
from pathlib import Path

from pyinfra.operations import files, systemd

from manage.preflight import validate_local_context
from manage.userconfig import setting

validate_local_context()
enabled = setting('fan_curve', True)
if not isinstance(enabled, bool):
    raise ValueError('fan_curve must be true or false')
source = Path(__file__).resolve().parents[1] / 'files/resource-policy'
files.directory(name='Fan controller helper directory', path='/usr/local/libexec',
                user='root', group='root', mode='755', _sudo=True)
helper = files.put(name='Earlier cooling controller', src=str(source / 't2-fan-curve.py'),
                   dest='/usr/local/libexec/t2-fan-curve', user='root', group='root', mode='755', _sudo=True)
unit = files.put(name='Earlier cooling service with watchdog and SMC recovery',
                 src=str(source / 't2-fan-curve.service'),
                 dest='/etc/systemd/system/t2-fan-curve.service',
                 user='root', group='root', mode='644', _sudo=True)
systemd.daemon_reload(name='Reload cooling service definition', _if=unit.did_change, _sudo=True)
systemd.service(name='Earlier cooling default' if enabled else 'Restore firmware cooling',
                service='t2-fan-curve.service', running=enabled, enabled=enabled, _sudo=True)
if enabled:
    systemd.service(name='Restart cooling after controller changes', service='t2-fan-curve.service',
                    restarted=True, _if=lambda: helper.did_change() or unit.did_change(), _sudo=True)
