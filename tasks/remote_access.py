"""Remote access: Tailscale (official repo), sshd at boot, fail2ban for sshd."""
import hashlib
import os
from pathlib import Path
import pwd
import shlex
import shutil
from io import StringIO

from pyinfra import logger
from pyinfra.operations import files, server, systemd
from manage.packages import PackageRequest, install_packages
from manage.preflight import validate_local_context

validate_local_context()
project = Path(__file__).resolve().parents[1]
src = project / 'files/remote-access'
home = Path(pwd.getpwuid(os.getuid()).pw_dir)
TAILSCALE_KEY_SHA256 = '3e03dacf222698c60b8e2f990b809ca1b3e104de127767864284e6c228f1fb39'
if hashlib.sha256((src / 'tailscale-archive-keyring.gpg').read_bytes()).hexdigest() != TAILSCALE_KEY_SHA256:
    raise RuntimeError('Tailscale archive key does not match the pinned sha256.')

# --- Tailscale -------------------------------------------------------------
key = files.put(name='Tailscale archive key', src=str(src / 'tailscale-archive-keyring.gpg'),
                dest='/usr/share/keyrings/tailscale-archive-keyring.gpg', mode='0644', _sudo=True)
repo = files.put(name='Tailscale apt source', src=str(src / 'tailscale.list'),
                 dest='/etc/apt/sources.list.d/tailscale.list', mode='0644', _sudo=True)
if not shutil.which('tailscale'):
    # The repo may not exist yet at preview time, so the guarded root helper
    # does the whole plan/scan/install after refreshing only this source.
    server.shell(
        name='Install tailscale (guarded)',
        commands=('apt-get update -o Dir::Etc::sourcelist=sources.list.d/tailscale.list '
                  '-o Dir::Etc::sourceparts=- -o APT::Get::List-Cleanup=0 && cd ' + shlex.quote(str(project))
                  + ' && /usr/bin/python3 -m manage.packages --apply tailscale'),
        _sudo=True,
    )
systemd.service(name='tailscaled at boot', service='tailscaled.service', running=True, enabled=True, _sudo=True)
logger.info('Tailscale: log in once with `sudo tailscale up` (prints a login URL).')
# The desktop's Tailscale tray switches the exit node as this user (no sudo): make the user
# the operator. With an exit node on, the LAN (printers, NAS, the VMs' host side) stays
# reachable; with it off, host and VM guests use the normal internet.
server.shell(
    name='Tailscale: desktop user is operator; exit node keeps LAN access',
    commands=[f'tailscale set --operator={pwd.getpwuid(os.getuid()).pw_name} --exit-node-allow-lan-access=true'],
    _if=lambda: shutil.which('tailscale') is not None, _sudo=True,
)

# --- sshd ------------------------------------------------------------------
install_packages(PackageRequest(packages=('openssh-server', 'fail2ban')))
keys = home / '.ssh/authorized_keys'
key_only = keys.is_file() and keys.stat().st_size > 0
if not key_only:
    logger.warning('No ~/.ssh/authorized_keys: SSH keeps password login (fail2ban protects it). '
                   'Add a key and re-run to switch to key-only.')
sshd_conf = files.put(
    name='sshd hardening drop-in', dest='/etc/ssh/sshd_config.d/10-t2-mac-kde.conf', mode='0644', _sudo=True,
    src=StringIO(
        '# Managed by t2-mac-kde\nPermitRootLogin no\nMaxAuthTries 4\nKbdInteractiveAuthentication no\n'
        f'PasswordAuthentication {"no" if key_only else "yes"}\n'),
)
systemd.service(name='Socket activation off (sshd runs as a normal service)', service='ssh.socket',
                running=False, enabled=False, _sudo=True)
systemd.service(name='sshd at boot', service='ssh.service', running=True, enabled=True, _sudo=True)
server.shell(name='Validate and reload sshd config', commands='/usr/sbin/sshd -t && systemctl reload ssh.service',
             _if=sshd_conf.did_change, _sudo=True)

# --- fail2ban --------------------------------------------------------------
jails = [files.put(name='fail2ban defaults + sshd jail', src=str(src / 'fail2ban-t2.conf'),
                   dest='/etc/fail2ban/jail.d/t2-mac-kde.conf', mode='0644', _sudo=True)]
# hypr-rdp 0.1.8 never logs the client IP on auth failure, so no RDP jail is possible;
# keep RDP on loopback/Tailscale instead.
systemd.service(name='fail2ban at boot', service='fail2ban.service', running=True, enabled=True, _sudo=True)
server.shell(name='Test and reload fail2ban config', commands='fail2ban-client -t && fail2ban-client reload',
             _if=lambda: any(op.did_change() for op in jails), _sudo=True)

# --- RDP reachable only over Tailscale (and loopback) ------------------------
rules = files.put(name='RDP firewall rules (Tailscale/loopback only)', src=str(src / 'rdp-tailscale-only.nft'),
                  dest='/etc/t2-mac-kde/rdp-tailscale-only.nft', mode='0644', create_remote_dir=True, _sudo=True)
unit = files.put(name='RDP firewall unit', src=str(src / 't2-rdp-firewall.service'),
                 dest='/etc/systemd/system/t2-rdp-firewall.service', mode='0644', _sudo=True)
systemd.service(name='RDP firewall at boot', service='t2-rdp-firewall.service', running=True, enabled=True,
                daemon_reload=True, _sudo=True)
server.shell(name='Reload RDP firewall rules', commands='systemctl restart t2-rdp-firewall.service',
             _if=lambda: rules.did_change() or unit.did_change(), _sudo=True)
