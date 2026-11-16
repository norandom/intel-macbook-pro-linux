"""Serialize managed apt calls and temporarily deny service starts when requested.

Only this exact deny-all helper is understood; foreign helpers are never executed
or overwritten. Native locks are probed and released before apt takes its own
locks. An unmanaged package-manager race therefore fails through apt normally.
"""
from contextlib import contextmanager
import fcntl
import time
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile

DENY_ALL = b'#!/bin/sh\n# t2-mac-kde: temporarily deny all service starts\nexit 101\n'
_RECEIPT = 'var/lib/t2-mac-kde/service-start-policy.json'
_POLICY = 'usr/sbin/policy-rc.d'


def _uid(root):
    return 0 if root == Path('/') else os.getuid()


def _regular(path, root, *, mode=None):
    info = path.lstat()
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != _uid(root)
            or info.st_mode & 0o022 or mode is not None and stat.S_IMODE(info.st_mode) != mode):
        raise RuntimeError('Unrecognized service policy/receipt ownership or permissions; restoration conflict.')
    return info


def inspect_service_policy(*, root=Path('/')):
    """Read-only preview admission. Existing interrupted transactions need apply recovery."""
    root = Path(root)
    policy = root / _POLICY
    if policy.exists() or policy.is_symlink():
        _regular(policy, root, mode=0o755)
        if policy.read_bytes() != DENY_ALL:
            raise RuntimeError('Foreign service-start policy blocks installation; no files were replaced.')


def _sync_directory(directory):
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _publish(root):
    """Stage complete bytes, persist prior absence/identity, then publish without replacement."""
    policy, receipt = root / _POLICY, root / _RECEIPT
    receipt.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    directory = receipt.parent.lstat()
    if (not stat.S_ISDIR(directory.st_mode) or directory.st_uid != _uid(root)
            or directory.st_mode & 0o022):
        raise RuntimeError('Unsafe package transaction state directory.')
    fd, temporary = tempfile.mkstemp(prefix='.t2-service-policy-', dir=policy.parent)
    stage = Path(temporary)
    try:
        with os.fdopen(fd, 'wb') as file:
            file.write(DENY_ALL)
            os.fchmod(file.fileno(), 0o755)
            file.flush()
            os.fsync(file.fileno())
        info = stage.stat()
        record = {'version': 1, 'prior_absent': True, 'stage': stage.name,
                  'device': info.st_dev, 'inode': info.st_ino,
                  'sha256': hashlib.sha256(DENY_ALL).hexdigest()}
        descriptor = os.open(receipt, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, 'w') as file:
            json.dump(record, file)
            file.flush()
            os.fsync(file.fileno())
        _sync_directory(receipt.parent)
        os.link(stage, policy, follow_symlinks=False)
        _sync_directory(policy.parent)
    except BaseException:
        # Once journaled, recovery owns cleanup; don't hide a conflicting policy.
        if not receipt.exists():
            stage.unlink(missing_ok=True)
        raise


def _recover(root):
    policy, receipt = root / _POLICY, root / _RECEIPT
    if not receipt.exists() and not receipt.is_symlink():
        return
    _regular(receipt, root, mode=0o600)
    try:
        record = json.loads(receipt.read_text())
        if (set(record) != {'version', 'prior_absent', 'stage', 'device', 'inode', 'sha256'}
                or record['version'] != 1 or record['prior_absent'] is not True
                or not isinstance(record['stage'], str)
                or not record['stage'].startswith('.t2-service-policy-')
                or '/' in record['stage']
                or record['sha256'] != hashlib.sha256(DENY_ALL).hexdigest()):
            raise ValueError('invalid receipt')
    except (ValueError, TypeError) as error:
        raise RuntimeError('Unrecognized transaction receipt; restoration conflict.') from error
    stage = policy.parent / record['stage']
    existing = []
    for path in (policy, stage):
        if not path.exists() and not path.is_symlink():
            continue
        info = _regular(path, root, mode=0o755)
        if ((info.st_dev, info.st_ino) != (record['device'], record['inode'])
                or path.read_bytes() != DENY_ALL):
            raise RuntimeError('Service policy was changed or replaced; restoration conflict.')
        existing.append(path)
    for path in existing:
        path.unlink()
    _sync_directory(policy.parent)
    receipt.unlink()
    _sync_directory(receipt.parent)


# Ubuntu's background apt runs take seconds to a few minutes.
LOCK_TIMEOUT = 300


def _probe_native_locks(root):
    descriptors = []
    try:
        for name in ('lock-frontend', 'lock'):
            fd = os.open(root / 'var/lib/dpkg' / name, os.O_RDWR | os.O_NOFOLLOW)
            descriptors.append(fd)
            fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    finally:
        for fd in descriptors:
            os.close(fd)


def _check_native_locks(root, timeout=LOCK_TIMEOUT):
    """Wait (up to timeout s) while another apt/dpkg run holds the lock, e.g. Ubuntu's apt-daily."""
    deadline = time.monotonic() + timeout
    waited = False
    while True:
        try:
            _probe_native_locks(root)
            return
        except OSError as error:
            if time.monotonic() >= deadline:
                raise RuntimeError('Native package-manager lock unavailable; retry after it completes.') from error
            if not waited:
                print(f'Another apt/dpkg run holds the lock; waiting up to {timeout} s ...', flush=True)
                waited = True
            time.sleep(2)


@contextmanager
def package_transaction(*, prevent_service_start=False, root=Path('/'), lock_timeout=None):
    """Hold the managed lock through apt and restore only verified owned state."""
    root = Path(root)
    lock = root / 'run/lock/t2-mac-kde-packages.lock'
    fd = os.open(lock, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        _regular(lock, root, mode=0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError('A concurrent managed package transaction is active.') from error
        _check_native_locks(root, LOCK_TIMEOUT if lock_timeout is None else lock_timeout)
        _recover(root)
        if prevent_service_start:
            inspect_service_policy(root=root)
        try:
            if prevent_service_start and not (root / _POLICY).exists():
                _publish(root)
            yield
        finally:
            _recover(root)
    finally:
        os.close(fd)
