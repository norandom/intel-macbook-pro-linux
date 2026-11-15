"""SSD health: smartd + daily NVMe check write alerts; new Bash shells show them.

TRIM (fstrim.timer) and e2scrub_all.timer are Ubuntu defaults and stay as they are.
"""
import os
from pathlib import Path
import pwd

from pyinfra.operations import files, systemd
from manage.packages import PackageRequest, install_packages
from manage.preflight import validate_local_context

validate_local_context()
home = Path(pwd.getpwuid(os.getuid()).pw_dir)
src = Path(__file__).resolve().parents[1] / 'files/storage-health'

install_packages(PackageRequest(packages=('smartmontools',)))

files.directory(name='Alert directory', path='/var/lib/t2-mac-kde/alerts', mode='0755', _sudo=True)
files.put(name='smartd alert hook', src=str(src / '50-t2-alert'),
          dest='/etc/smartmontools/run.d/50-t2-alert', mode='0755', _sudo=True)
smartd_conf = files.line(
    name='smartd: also warn on SSD temperature (65 C info, 75 C critical)',
    path='/etc/smartd.conf', line=r'^DEVICESCAN.*',
    replace='DEVICESCAN -d removable -n standby -W 4,65,75 -m root -M exec /usr/share/smartmontools/smartd-runner',
    _sudo=True,
)
systemd.service(name='Restart smartd after config change', service='smartmontools.service',
                running=True, enabled=True, restarted=True, _if=smartd_conf.did_change, _sudo=True)

files.put(name='Daily NVMe health check script', src=str(src / 't2-storage-health'),
          dest='/usr/local/sbin/t2-storage-health', mode='0755', _sudo=True)
[files.put(name=f'Install {unit}', src=str(src / unit), dest=f'/etc/systemd/system/{unit}',
                   mode='0644', _sudo=True) for unit in ('t2-storage-health.service', 't2-storage-health.timer')]
systemd.service(name='Enable daily NVMe health timer', service='t2-storage-health.timer', running=True,
                enabled=True, daemon_reload=True, _sudo=True)

files.put(name='t2-alerts command', src=str(src / 't2-alerts'), dest=str(home / '.local/bin/t2-alerts'), mode='0755')
files.block(
    name='Show system alerts in new interactive Bash shells',
    path=str(home / '.bashrc'),
    marker='# {mark} t2-mac-kde system alerts',
    content='case $- in *i*) [ -x "$HOME/.local/bin/t2-alerts" ] && "$HOME/.local/bin/t2-alerts" --brief ;; esac',
    backup=True,
)
