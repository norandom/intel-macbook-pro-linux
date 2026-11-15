"""Disposable apt policy fixtures: never write live /etc or invoke sudo."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from manage import package_policy as policy

CONTENT = b'Package: snapd flatpak\nPin: version *\nPin-Priority: -1\n'


def output(package, priority=-1, candidate='(none)'):
    return (f'{package}:\n  Installed: (none)\n  Candidate: {candidate}\n  Version table:\n'
            f'     2.0 {priority} (phased 20%)\n        500 https://archive.ubuntu.com stable/main amd64 Packages\n'
            f'     1.0 {priority}\n        500 https://archive.ubuntu.com stable/main amd64 Packages\n')


class EffectivePolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.directory = self.root / 'etc/apt/preferences.d'
        self.directory.mkdir(parents=True)
        self.owned = self.directory / '90-t2-package-policy.pref'
        self.nosnap = self.directory / 'nosnap.pref'
        self.nosnap.write_bytes(b'Package: snapd\nPin: release a=*\nPin-Priority: -10\n')
        self.nosnap.chmod(0o640)
        self.status = self.root / 'var/lib/dpkg/status'
        self.status.parent.mkdir(parents=True)
        self.status.write_text('')
        self.runner = patch.object(policy.subprocess, 'run', side_effect=self.run_command)
        self.runner.start()
        self.addCleanup(self.runner.stop)
        self.outputs = {}
        self.calls = []

    def run_command(self, argv, **kwargs):
        self.calls.append(argv)
        if argv[0] == '/usr/bin/apt-config':
            return subprocess.CompletedProcess(argv, 0, "policy_root='/'\npolicy_etc='etc/apt'\npolicy_main='preferences'\npolicy_parts='preferences.d'\n", '')
        self.assertEqual(argv[0], '/usr/bin/apt-cache')
        self.assertEqual(set(kwargs['env']), {'PATH', 'LC_ALL', 'LANG'})
        self.assertEqual(kwargs['env']['LC_ALL'], 'C')
        self.assertEqual(kwargs['timeout'], 30)
        self.assertNotIn('shell', kwargs)
        self.assertTrue(argv[-1].endswith(':*'))
        package = argv[-1][:-2]
        for arg in argv:
            if arg.startswith('Dir::Etc::preferencesparts='):
                overlay = Path(arg.split('=', 1)[1])
                self.assertEqual((overlay / self.nosnap.name).read_bytes(), self.nosnap.read_bytes())
                self.assertEqual((overlay / self.owned.name).read_bytes(), CONTENT)
        return subprocess.CompletedProcess(argv, 0, self.outputs.get(package, output(package)), '')

    def verify(self, preview=False):
        return policy.verify_effective_policy(preview=preview, root=self.root)

    def test_preview_preserves_all_live_preferences_bytes_and_modes(self):
        self.owned.write_bytes(b'old owned policy')
        self.owned.chmod(0o600)
        original = self.directory.parent / 'preferences'
        original.write_bytes(b'Package: other\nPin: version *\nPin-Priority: 50\n')
        before = {str(p): (p.read_bytes(), p.stat().st_mode) for p in (self.owned, self.nosnap, original)}
        self.verify(preview=True)
        self.assertEqual(before, {str(p): (p.read_bytes(), p.stat().st_mode) for p in (self.owned, self.nosnap, original)})
        self.assertEqual(len(self.calls), 3)
        self.assertFalse(policy.backup_path(self.root).exists())

    def test_actual_verification_requires_owned_exact_content_even_without_candidates(self):
        self.outputs = {'snapd': '', 'flatpak': ''}
        with self.assertRaisesRegex(RuntimeError, 'owned|policy'):
            self.verify()
        self.owned.write_bytes(CONTENT)
        self.verify()

    def test_conflicts_in_any_available_version_and_candidate_block(self):
        for result in (output('snapd', 1001), output('snapd').replace('1.0 -1', '1.0 500'),
                       output('snapd', -1, '2.0'), 'snapd:\n  Candidate: (none)\n  Version table:\n junk\n'):
            with self.subTest(result=result):
                self.outputs['snapd'] = result
                with self.assertRaises(RuntimeError):
                    self.verify(preview=True)

    def test_foreign_architecture_with_positive_pin_blocks(self):
        self.outputs['snapd'] = output('snapd') + output('snapd:i386', 1001)
        with self.assertRaisesRegex(RuntimeError, 'pin'):
            self.verify(preview=True)

    def test_native_phased_negative_priorities_accepted(self):
        self.outputs['snapd'] = output('snapd', -10)
        self.verify(preview=True)

    def test_installed_and_incomplete_runtimes_block_without_purge(self):
        for status in ('install ok installed', 'install ok unpacked', 'install reinstreq half-configured'):
            for name in ('snapd', 'flatpak'):
                self.status.write_text(f'Package: {name}\nStatus: {status}\nArchitecture: amd64\n\n')
                with self.subTest(status=status, name=name), self.assertRaisesRegex(RuntimeError, 'remediation pending'):
                    self.verify(preview=True)
        self.assertEqual(self.calls, [])

    def test_removed_config_only_package_is_not_installed(self):
        self.status.write_text('Package: snapd\nStatus: deinstall ok config-files\n\n')
        self.verify(preview=True)

    def test_apply_noop_and_backup_restore_preserve_original_bytes_mode(self):
        self.owned.write_bytes(b'previous policy\n')
        self.owned.chmod(0o600)
        original_nosnap = (self.nosnap.read_bytes(), self.nosnap.stat().st_mode)
        self.assertTrue(policy.apply_policy(root=self.root))
        self.assertEqual(self.owned.read_bytes(), CONTENT)
        self.assertFalse(policy.apply_policy(root=self.root))
        self.assertTrue(policy.restore_policy(root=self.root))
        self.assertEqual(self.owned.read_bytes(), b'previous policy\n')
        self.assertEqual(self.owned.stat().st_mode & 0o777, 0o600)
        self.assertEqual((self.nosnap.read_bytes(), self.nosnap.stat().st_mode), original_nosnap)

    def test_restore_absent_original_and_refuse_foreign_content(self):
        policy.apply_policy(root=self.root)
        self.owned.write_bytes(b'new administrator content')
        with self.assertRaisesRegex(RuntimeError, 'changed|foreign'):
            policy.restore_policy(root=self.root)
        self.assertEqual(self.owned.read_bytes(), b'new administrator content')
        self.owned.write_bytes(CONTENT)
        policy.restore_policy(root=self.root)
        self.assertFalse(self.owned.exists())

    def test_apply_verification_failure_restores_original(self):
        self.owned.write_bytes(b'original')
        self.owned.chmod(0o600)
        def run(argv, **kwargs):
            if argv[0] == '/usr/bin/apt-cache' and not any(str(a).startswith('Dir::Etc::preferencesparts=') for a in argv):
                return subprocess.CompletedProcess(argv, 0, output(argv[-1][:-2], 500), '')
            return self.run_command(argv, **kwargs)
        with patch.object(policy.subprocess, 'run', side_effect=run):
            with self.assertRaises(RuntimeError):
                policy.apply_policy(root=self.root)
        self.assertEqual(self.owned.read_bytes(), b'original')
        self.assertEqual(self.owned.stat().st_mode & 0o777, 0o600)

    def test_symlinks_and_stale_backup_rejected_without_overwrite(self):
        self.owned.symlink_to(self.nosnap)
        with self.assertRaises(RuntimeError):
            policy.apply_policy(root=self.root)
        self.owned.unlink()
        policy.backup_path(self.root).parent.mkdir(parents=True)
        policy.backup_path(self.root).write_bytes(b'foreign')
        with self.assertRaises(RuntimeError):
            policy.apply_policy(root=self.root)
        self.assertEqual(policy.backup_path(self.root).read_bytes(), b'foreign')

    def test_redirected_preferences_block_even_if_candidates_absent(self):
        result = subprocess.CompletedProcess([], 0,
            "policy_root='/'\npolicy_etc='etc/apt'\npolicy_main='preferences'\npolicy_parts='/tmp/ignored-pins'\n", '')
        with patch.object(policy.subprocess, 'run', return_value=result):
            with self.assertRaisesRegex(RuntimeError, 'redirected'):
                self.verify(preview=True)

    def test_command_failures_and_stderr_are_not_success(self):
        for result in (subprocess.CompletedProcess([], 100, '', 'failed'), subprocess.CompletedProcess([], 0, '', 'warning')):
            with patch.object(policy.subprocess, 'run', return_value=result), self.assertRaises(RuntimeError):
                self.verify(preview=True)
        with patch.object(policy.subprocess, 'run', side_effect=subprocess.TimeoutExpired('apt-cache', 30)), self.assertRaises(RuntimeError):
            self.verify(preview=True)

    def test_repository_asset_matches_owned_content(self):
        self.assertEqual(Path('files/apt/90-t2-package-policy.pref').read_bytes(), CONTENT)


class PolicySchedulingTests(unittest.TestCase):
    def deploy(self, matching=False, error=None):
        import runpy
        with patch('manage.preflight.validate_local_context') as preflight, \
             patch.object(policy, 'verify_effective_policy', side_effect=error) as verify, \
             patch('pyinfra.operations.server.shell') as operation, \
             patch.object(Path, 'is_file', return_value=matching), \
             patch.object(Path, 'read_bytes', return_value=CONTENT):
            if error:
                with self.assertRaises(RuntimeError):
                    runpy.run_path('tasks/package_policy.py')
            else:
                runpy.run_path('tasks/package_policy.py')
            preflight.assert_called_once_with()
            return verify, operation

    def test_unmatched_policy_schedules_apply_without_performing_it(self):
        verify, operation = self.deploy()
        verify.assert_called_once_with(preview=True)
        operation.assert_called_once()
        self.assertTrue(operation.call_args.kwargs['_sudo'])
        command = operation.call_args.kwargs['commands']
        self.assertTrue(command.startswith('/usr/bin/python3 '))
        self.assertTrue(command.endswith('manage/package_policy.py --apply'))

    def test_matching_policy_verifies_without_scheduling_changes(self):
        verify, operation = self.deploy(matching=True)
        self.assertEqual(verify.call_count, 2)
        self.assertEqual(verify.call_args.kwargs, {})
        operation.assert_not_called()

    def test_policy_failure_prevents_scheduling(self):
        _, operation = self.deploy(error=RuntimeError('conflicting effective pin'))
        operation.assert_not_called()
