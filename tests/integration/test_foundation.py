"""Native apt/dpkg integration in disposable user/mount namespaces.

The host root is read-only. Every writable package/configuration path is bound
to one TemporaryDirectory; test-time sudo enters a mapped-root user namespace.
No host sudo, package installation, service or network is used.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import socketserver
import subprocess
import tempfile
import threading
import unittest


PROJECT = Path(__file__).resolve().parents[2]

PROTECTED = ('/etc/fstab', '/etc/crypttab', '/etc/initramfs-tools/modules',
             '/etc/modprobe.d/apple-gmux.conf', '/etc/udev/rules.d/30-amdgpu-pm.rules',
             '/etc/sddm.conf', '/etc/sddm.conf.d', '/boot', '/usr/lib/modules',
             '/usr/lib/firmware', '/usr/share/alsa/ucm2')


def protected_snapshot():
    observations = {}
    for name in PROTECTED:
        path = Path(name)
        try:
            info = path.lstat()
            digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
            observations[name] = (info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, digest)
        except FileNotFoundError:
            observations[name] = 'absent'
        except PermissionError:
            observations[name] = 'unreadable'
    return observations


class UbuntuFixture:
    def __init__(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='t2-foundation-integration-')
        self.root = Path(self.temporary.name)
        self.home = Path.home()
        self.bindings = {
            '/var/lib': 'var-lib', '/etc/apt': 'apt', '/var/lib/dpkg': 'dpkg', '/var/lib/apt': 'apt-state',
            '/var/cache/apt': 'apt-cache', '/var/log': 'log', '/opt': 'opt',
            '/run/lock': 'lock', '/var/lib/t2-mac-kde': 'receipts', str(self.home): 'home',
        }
        for name in self.bindings.values():
            (self.root / name).mkdir()
        for name in ('repo', 'bin', 'hooks', 'apt/preferences.d', 'apt/apt.conf.d',
                     'dpkg/info', 'dpkg/triggers', 'dpkg/updates', 'apt-state/lists/partial',
                     'apt-cache/archives/partial', 'log/apt'):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        for name in ('status', 'available', 'lock', 'lock-frontend'):
            (self.root / 'dpkg' / name).touch()
        (self.root / 'dpkg/triggers/Unincorp').touch()
        (self.root / 'apt/apt.conf.d/00-fixture').write_text(
            'APT::Sandbox::User "root";\nAcquire::Languages "none";\n')
        (self.root / 'apt/preferences.d/nosnap.pref').write_text(
            'Package: snapd\nPin: release a=*\nPin-Priority: -10\n')
        self._repository()
        self._shell()
        wrapper = ('#!/usr/bin/python3\nimport json,socket,sys\n'
                   'arguments=sys.argv[1:]\n'
                   'while arguments and arguments[0] in ("-H","-n","-E"): arguments.pop(0)\n'
                   f's=socket.socket(socket.AF_UNIX); s.connect({str(self.root / "auth.sock")!r})\n'
                   's.sendall(json.dumps(arguments).encode()+b"\\n")\n'
                   'result=json.loads(s.makefile("r").readline())\n'
                   'sys.stdout.write(result["stdout"]); sys.stderr.write(result["stderr"])\n'
                   'sys.exit(result["returncode"])\n')
        (self.root / 'bin/sudo').write_text(wrapper)
        (self.root / 'bin/sudo').chmod(0o755)
        self.run(['/usr/bin/apt-get', 'update'], privileged=True, check=True)
        baseline = self.run(['/usr/bin/python3', '-c',
                             'from manage.packages import _baseline_digest; print(_baseline_digest())'],
                            check=True).stdout.strip()
        review = dict(package='fixture-cli', version='1.0', architecture='all',
                      deb_sha256=self.deb_hash, baseline_sha256=baseline,
                      evidence='disposable fixture: no scripts, triggers or dependencies; only /opt payload',
                      native=True, scripts_reviewed=True, triggers_reviewed=True,
                      apt_hooks_reviewed=True, paths=['/opt/t2-fixture/fixture-cli'])
        dependent = dict(review, package='fixture-dependent',
                         deb_sha256=self.archives['fixture-dependent'],
                         paths=['/opt/t2-fixture/fixture-dependent'])
        (self.root / 'review.json').write_text(json.dumps([review, dependent]))
        self.deploy = self.root / 'deploy.py'
        self.deploy.write_text('from pyinfra import local\n'
                              'from manage.packages import PackageRequest, install_packages\n'
                              'local.include("tasks/node.py")\n'
                              'local.include("tasks/package_policy.py")\n'
                              'install_packages(PackageRequest(("fixture-cli",), "ubuntu"))\n')
        fixture = self
        class Authenticate(socketserver.StreamRequestHandler):
            def handle(self):
                arguments = json.loads(self.rfile.readline())
                if arguments[0] not in ('sh', 'bash', '/bin/sh', '/bin/bash'):
                    raise ValueError('Unexpected fixture authentication command')
                result = fixture.run(arguments, privileged=True)
                self.wfile.write(json.dumps(dict(returncode=result.returncode, stdout=result.stdout,
                                                stderr=result.stderr)).encode() + b'\n')
        self.server = socketserver.ThreadingUnixStreamServer(str(self.root / 'auth.sock'), Authenticate)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temporary.cleanup()

    def namespace(self, *, root=False):
        command = ['bwrap', '--ro-bind', '/', '/', '--dev', '/dev', '--proc', '/proc',
                   '--unshare-user', '--unshare-pid', '--unshare-net', '--die-with-parent',
                   '--uid', '0' if root else str(os.getuid()),
                   '--gid', '0' if root else str(os.getgid()), '--tmpfs', '/tmp',
                   '--bind', str(self.root), str(self.root)]
        for target, source in self.bindings.items():
            command += ['--bind', str(self.root / source), target]
        # The home bind intentionally hides all real user configuration; expose
        # only the current project so its interpreter and deploy files run.
        command += ['--ro-bind', str(PROJECT), str(PROJECT)]
        if (self.root / 'review.json').exists():
            command += ['--ro-bind', str(self.root / 'review.json'),
                        str(PROJECT / 'files/package-reviews/ubuntu-cli.json')]
        command += ['--chdir', str(PROJECT),
                    '--setenv', 'HOME', str(self.home),
                    '--setenv', 'PATH', f'{self.root}/bin:/usr/sbin:/usr/bin:/sbin:/bin',
                    '--setenv', 'PYTHONPATH', f'{self.root}/hooks:{PROJECT}']
        return command

    def run(self, arguments, *, privileged=False, check=False):
        result = subprocess.run(self.namespace(root=privileged) + arguments,
                                text=True, capture_output=True, timeout=60)
        if check and result.returncode:
            raise AssertionError(result.stdout + result.stderr)
        return result

    def pyinfra(self, *, dry=False, deploy=None):
        return self.run([str(PROJECT / '.venv/bin/python'), '-m', 'pyinfra', '@local',
                         str(deploy or self.deploy), '--dry' if dry else '-y'])

    def snapshot(self):
        # Compare managed state, not native apt's inspection caches/planner logs.
        return {str(path.relative_to(self.root)): (path.stat().st_mode & 0o777, path.read_bytes())
                for name in self.bindings.values() if name not in ('log', 'apt-cache')
                for path in (self.root / name).rglob('*')
                if path.is_file() and path.name not in ('lock', 'lock-frontend', 'Lock')}

    def _repository(self):
        index = ''
        self.archives = {}
        for name in ('fixture-cli', 'snapd', 'flatpak', 'fixture-dependent'):
            package = self.root / ('package-' + name)
            (package / 'DEBIAN').mkdir(parents=True)
            control = (f'Package: {name}\nVersion: 1.0\nArchitecture: all\n'
                       'Maintainer: Fixture <fixture@example.invalid>\n'
                       'Origin: Ubuntu\nDescription: Disposable foundation integration payload\n')
            if name == 'fixture-dependent':
                control += 'Depends: flatpak\n'
            (package / 'DEBIAN/control').write_text(control)
            (package / 'opt/t2-fixture').mkdir(parents=True)
            (package / 'opt/t2-fixture' / name).write_text('fixture installed\n')
            deb = self.root / f'repo/{name}_1.0_all.deb'
            subprocess.run(['dpkg-deb', '--root-owner-group', '--build', str(package), str(deb)],
                           check=True, capture_output=True)
            digest = hashlib.sha256(deb.read_bytes()).hexdigest()
            self.archives[name] = digest
            index += control + f'Filename: ./{deb.name}\nSize: {deb.stat().st_size}\nSHA256: {digest}\n\n'
        self.deb_hash = self.archives['fixture-cli']
        (self.root / 'repo/Packages').write_text(index)
        release = ('Origin: Ubuntu\nLabel: Ubuntu\nSuite: resolute\nCodename: resolute\nVersion: 26.04\n'
                   'Date: Sun, 15 Nov 2026 00:00:00 UTC\nArchitectures: amd64 all\nSHA256:\n')
        release += f' {hashlib.sha256(index.encode()).hexdigest()} {len(index.encode())} Packages\n'
        (self.root / 'repo/Release').write_text(release)
        (self.root / 'apt/sources.list').write_text(f'deb [trusted=yes] file:{self.root}/repo ./\n')

    def _shell(self):
        home = self.root / 'home'
        version = (PROJECT / '.nvmrc').read_text().strip()
        runtime = home / f'.nvm/versions/node/v{version}/bin'
        runtime.mkdir(parents=True)
        for tool in ('node', 'npm', 'npx'):
            path = runtime / tool
            path.write_text('#!/bin/sh\nexit 0\n')
            path.chmod(0o755)
        (home / '.nvm/alias').mkdir()
        (home / '.nvm/alias/default').write_text(version + '\n')
        (home / '.nvm/nvm.sh').write_text(
            f'nvm() {{ case "$1" in --version) echo 0.41.0;; version) echo v{version};; *) return 1;; esac; }}\n')
        (home / '.bashrc').write_text('export USER_SETTING=preserved\n')


@unittest.skipUnless(shutil.which('bwrap') and shutil.which('dpkg-deb'), 'bubblewrap and dpkg-deb required')
class FoundationIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.getuid() == 0:
            raise unittest.SkipTest('integration requires a real desktop-user controller')
        probe = subprocess.run(['bwrap', '--ro-bind', '/', '/', '--dev', '/dev', '--proc', '/proc',
                                '--unshare-user', '--unshare-pid', '--unshare-net', '--die-with-parent',
                                '/bin/true'], capture_output=True, text=True)
        if probe.returncode:
            raise unittest.SkipTest('user namespaces unavailable; integration verification remains pending')

    def fixture(self):
        try:
            fixture = UbuntuFixture()
        except AssertionError as error:
            if 'No permissions to create a new namespace' in str(error):
                self.skipTest('user namespaces unavailable; run the integration suite outside the restricted sandbox')
            raise
        self.addCleanup(fixture.close)
        return fixture

    def test_preview_apply_repeat_and_scoped_restore_preserve_protected_baseline(self):
        fixture = self.fixture()
        protected = protected_snapshot()
        mounts = fixture.run(['/usr/bin/python3', '-c',
                              'import os; from pathlib import Path; '
                              f'assert all(os.statvfs(p).f_flag & os.ST_RDONLY for p in {PROTECTED!r} if Path(p).exists())'],
                             privileged=True)
        self.assertEqual(mounts.returncode, 0, mounts.stdout + mounts.stderr)
        before = fixture.snapshot()
        preview = fixture.pyinfra(dry=True)
        self.assertEqual(preview.returncode, 0, preview.stdout + preview.stderr)
        self.assertEqual(before, fixture.snapshot())
        node_preview = fixture.pyinfra(dry=True, deploy=PROJECT / 'tasks/node.py')
        self.assertEqual(node_preview.returncode, 0, node_preview.stdout + node_preview.stderr)
        self.assertEqual(before, fixture.snapshot())
        applied = fixture.pyinfra()
        self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
        self.assertEqual((fixture.root / 'opt/t2-fixture/fixture-cli').read_text(), 'fixture installed\n')
        installed = fixture.snapshot()
        repeated = fixture.pyinfra()
        self.assertEqual(repeated.returncode, 0, repeated.stdout + repeated.stderr)
        self.assertEqual(installed, fixture.snapshot())
        self.assertIn('No changes', repeated.stdout + repeated.stderr)
        restore = fixture.run(['/usr/bin/python3', '-c',
                               'from manage.package_policy import restore_policy; restore_policy()'],
                              privileged=True)
        self.assertEqual(restore.returncode, 0, restore.stdout + restore.stderr)
        restored_bash = fixture.pyinfra(deploy=PROJECT / 'tasks/node_restore.py')
        self.assertEqual(restored_bash.returncode, 0, restored_bash.stdout + restored_bash.stderr)
        self.assertNotIn('NVM_DIR', (fixture.root / 'home/.bashrc').read_text())
        self.assertIn('USER_SETTING=preserved', (fixture.root / 'home/.bashrc').read_text())
        self.assertEqual((fixture.root / 'apt/preferences.d/nosnap.pref').read_bytes(),
                         before['apt/preferences.d/nosnap.pref'][1])
        self.assertFalse((fixture.root / 'apt/preferences.d/90-t2-package-policy.pref').exists())
        self.assertEqual(protected, protected_snapshot())

    def test_authentication_failure_keeps_prior_success_and_nonzero_status(self):
        fixture = self.fixture()
        (fixture.root / 'bin/sudo').write_text('#!/bin/sh\necho "fixture authentication denied" >&2\nexit 1\n')
        result = fixture.pyinfra()
        self.assertNotEqual(result.returncode, 0)
        output = result.stdout + result.stderr
        self.assertIn('fixture authentication denied', output)
        self.assertIn('Load nvm and user tools in Bash', output)
        self.assertIn('NVM_DIR', (fixture.root / 'home/.bashrc').read_text())
        self.assertFalse((fixture.root / 'opt/t2-fixture/fixture-cli').exists())

    def test_download_failure_is_nonzero_and_does_not_fallback(self):
        fixture = self.fixture()
        (fixture.root / 'repo/fixture-cli_1.0_all.deb').unlink()
        result = fixture.pyinfra()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((fixture.root / 'opt/t2-fixture/fixture-cli').exists())
        self.assertIn('fixture-cli', result.stdout + result.stderr)

    def test_installed_prohibited_runtime_blocks_without_purge(self):
        fixture = self.fixture()
        status = fixture.root / 'dpkg/status'
        content = ('Package: snapd\nStatus: install ok installed\nVersion: 1.0\n'
                   'Architecture: all\nDescription: Fixture installed runtime\n\n')
        status.write_text(content)
        before = fixture.snapshot()
        result = fixture.pyinfra()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('snapd', result.stdout + result.stderr)
        self.assertEqual(before, fixture.snapshot())

    def test_conflicting_administrator_pin_blocks_without_rewriting_it(self):
        fixture = self.fixture()
        (fixture.root / 'apt/preferences.d/00-administrator.pref').write_text(
            'Package: snapd\nPin: version *\nPin-Priority: 1001\n')
        before = fixture.snapshot()
        result = fixture.pyinfra()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('snapd', result.stdout + result.stderr)
        self.assertEqual(before, fixture.snapshot())

    def test_prohibited_requested_and_transitive_packages_block_before_operations(self):
        fixture = self.fixture()
        for selection in ('snapd', 'fixture-dependent'):
            with self.subTest(selection=selection):
                deploy = fixture.root / 'blocked.py'
                deploy.write_text('from manage.packages import PackageRequest, install_packages\n'
                                  f'install_packages(PackageRequest(({selection!r},), "ubuntu"))\n')
                before = fixture.snapshot()
                result = fixture.pyinfra(deploy=deploy)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('snapd' if selection == 'snapd' else 'flatpak', result.stdout + result.stderr)
                self.assertEqual(before, fixture.snapshot())
