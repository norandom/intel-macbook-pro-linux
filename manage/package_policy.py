"""Own one apt preference file; never purge runtimes or edit administrator pins.

``verify_effective_policy(preview=False)`` is the read-only admission gate for
package installation. Call it again immediately before any install. Preview uses
an ephemeral copy of ALL existing preferences with only our file replaced.
``apply_policy`` and ``restore_policy`` are explicit mutation entry points.
"""
from base64 import b64decode, b64encode
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import shlex
import stat
import subprocess
import tempfile

CONTENT = b"Package: snapd flatpak\nPin: version *\nPin-Priority: -1\n"
NAME = "90-t2-package-policy.pref"
_ENV = {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LC_ALL": "C", "LANG": "C"}


def backup_path(root: Path = Path('/')) -> Path:
    return Path(root) / 'var/lib/t2-mac-kde/package-policy-backup.json'


def _owned(root):
    return Path(root) / 'etc/apt/preferences.d' / NAME


def _regular(path):
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise RuntimeError(f'Unsafe nonregular policy path: {path}')


def _installed(root):
    status = Path(root) / 'var/lib/dpkg/status'
    try:
        text = status.read_text()
    except OSError as error:
        raise RuntimeError('Cannot inspect dpkg status; package policy unresolved') from error
    for paragraph in text.split('\n\n'):
        fields = dict(line.split(': ', 1) for line in paragraph.splitlines() if ': ' in line and not line.startswith(' '))
        if fields.get('Package', '').split(':')[0] in ('snapd', 'flatpak'):
            if fields.get('Status', '').split()[-1:] not in (['not-installed'], ['config-files']):
                raise RuntimeError(f"Existing prohibited runtime {fields['Package']}; remediation pending (no automatic purge)")


def _check_output(package, output):
    # A package absent from indexes prints nothing; the mandatory exact owned
    # configuration remains evidence, independent of candidate availability.
    if not output.strip():
        return
    lines = output.splitlines()
    if lines[0] != package + ':' or '  Candidate: (none)' not in lines or '  Installed: (none)' not in lines:
        raise RuntimeError(f'Effective policy conflict for {package}; remediation pending')
    table = False
    for line in lines[1:]:
        if line == '  Version table:':
            table = True
            continue
        if not table or not line.strip():
            continue
        version = re.fullmatch(r'\s+(?:\*\*\* )?(\S+)\s+(-?\d+)(?: \(phased \d+%\))?\s*', line)
        if version:
            if int(version[2]) >= 0:
                raise RuntimeError(f'Overriding administrator pin permits {package} {version[1]}; remediation pending')
        elif not re.fullmatch(r'\s+-?\d+\s+\S+.*', line):
            raise RuntimeError(f'Unrecognized apt policy for {package}: {line}')
    if not table:
        raise RuntimeError(f'Missing version table for {package}')


def _verify_config_paths():
    # With empty indexes no candidate table can expose a redirected preferences
    # directory. Verify apt actually reads the configuration that we own.
    command = ('/usr/bin/apt-config', 'shell', 'policy_root', 'Dir',
               'policy_etc', 'Dir::Etc', 'policy_main', 'Dir::Etc::preferences',
               'policy_parts', 'Dir::Etc::preferencesparts')
    try:
        result = subprocess.run(command, env=_ENV, capture_output=True, text=True, timeout=30)
        values = dict(part.split('=', 1) for part in shlex.split(result.stdout))
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        raise RuntimeError('Cannot verify active apt preference configuration') from error
    expected = {'policy_root', 'policy_etc', 'policy_main', 'policy_parts'}
    if result.returncode or result.stderr.strip() or set(values) != expected:
        raise RuntimeError('Cannot verify active apt preference configuration')
    base = Path(values['policy_root']) / values['policy_etc']
    if (str(base / values['policy_main']) != '/etc/apt/preferences'
            or str(base / values['policy_parts']) != '/etc/apt/preferences.d'):
        raise RuntimeError('Administrator redirected active apt preferences; remediation pending')


def _verify(root, options=()):
    for package in ('snapd', 'flatpak'):
        command = ('/usr/bin/apt-cache', '-o', 'Dir::Cache::pkgcache=', '-o', 'Dir::Cache::srcpkgcache=',
                   *options, 'policy', package + ':*')
        try:
            result = subprocess.run(command, env=_ENV, capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.SubprocessError) as error:
            raise RuntimeError(f'Cannot verify effective policy for {package}') from error
        if result.returncode or result.stderr.strip():
            raise RuntimeError(f'apt-cache policy failed for {package}: {result.stderr.strip()}')
        # apt-cache's architecture glob covers foreign architectures as well
        # as native versions. Each returned package table must be prohibited.
        for block in re.split(r'(?m)(?=^[^\s])', result.stdout):
            if not block.strip():
                continue
            header = block.splitlines()[0]
            if not re.fullmatch(re.escape(package) + r'(?::[a-z0-9-]+)?:', header):
                raise RuntimeError(f'Unexpected package in apt policy: {header}')
            _check_output(header[:-1], block)


def verify_effective_policy(*, preview=False, root=Path('/')) -> None:
    """Verify config AND every available version; never write host preferences.

    ``root`` exists for disposable filesystem fixtures, not remote deployment.
    Native apt indexes remain read-only. Actual deployment always uses /.
    """
    root = Path(root)
    owned = _owned(root)
    _regular(owned)
    _installed(root)
    _verify_config_paths()
    if not preview:
        if not owned.exists() or owned.read_bytes() != CONTENT:
            raise RuntimeError('Exact owned package policy is missing or changed')
        _verify(root)
        return
    with tempfile.TemporaryDirectory(prefix='t2-apt-policy-') as temporary:
        overlay = Path(temporary)
        parts = overlay / 'preferences.d'
        parts.mkdir()
        directory = owned.parent
        if directory.exists():
            for path in directory.iterdir():
                _regular(path)
                shutil.copyfile(path, parts / path.name)
        (parts / NAME).write_bytes(CONTENT)
        main = root / 'etc/apt/preferences'
        _regular(main)
        (overlay / 'preferences').write_bytes(main.read_bytes() if main.exists() else b'')
        _verify(root, ('-o', f'Dir::Etc::preferences={overlay / "preferences"}',
                       '-o', f'Dir::Etc::preferencesparts={parts}'))


def _replace(path, data, mode, uid=None, gid=None):
    # Same-directory replace avoids partial policy files on interruption.
    descriptor, temporary = tempfile.mkstemp(prefix='.t2-policy-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
            os.fchmod(stream.fileno(), mode)
            if uid is not None:
                os.fchown(stream.fileno(), uid, gid)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def apply_policy(*, root=Path('/')) -> bool:
    """Apply only the owned file, backing it up and restoring on validation failure."""
    root = Path(root)
    verify_effective_policy(preview=True, root=root)
    owned = _owned(root)
    if owned.exists() and owned.read_bytes() == CONTENT:
        verify_effective_policy(root=root)
        return False
    backup = backup_path(root)
    _regular(backup)
    if backup.exists():
        raise RuntimeError('Existing policy backup requires explicit restoration; refusing overwrite')
    original = None
    if owned.exists():
        info = owned.stat()
        original = dict(data=b64encode(owned.read_bytes()).decode(), mode=stat.S_IMODE(info.st_mode),
                        uid=info.st_uid, gid=info.st_gid)
    backup.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation preserves any prior recovery record.
    with backup.open('x') as stream:
        os.fchmod(stream.fileno(), 0o600)
        json.dump(dict(original=original, managed_sha256=hashlib.sha256(CONTENT).hexdigest()), stream)
        stream.flush()
        os.fsync(stream.fileno())
    owned.parent.mkdir(parents=True, exist_ok=True)
    _replace(owned, CONTENT, 0o644)
    try:
        verify_effective_policy(root=root)
    except Exception:
        restore_policy(root=root)
        raise
    return True


def restore_policy(*, root=Path('/')) -> bool:
    """Restore our last replacement only if the owned bytes still match ours."""
    root = Path(root)
    owned, backup = _owned(root), backup_path(root)
    _regular(owned)
    _regular(backup)
    if not backup.exists():
        return False
    record = json.loads(backup.read_text())
    if (not owned.exists() or owned.read_bytes() != CONTENT
            or record['managed_sha256'] != hashlib.sha256(CONTENT).hexdigest()):
        raise RuntimeError('Owned policy changed to foreign content; refusing restoration')
    original = record['original']
    if original is None:
        owned.unlink()
    else:
        _replace(owned, b64decode(original['data'], validate=True), original['mode'], original['uid'], original['gid'])
    backup.unlink()
    return True


if __name__ == '__main__':
    import sys
    if sys.argv[1:] == ['--apply']:
        apply_policy()
    elif sys.argv[1:] == ['--restore']:
        restore_policy()
    else:
        raise SystemExit('Usage: package_policy.py --apply|--restore')
