"""Guard integration: no test invokes native apt or sudo."""
from contextlib import nullcontext
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from manage import packages as guard


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.request = guard.PackageRequest(('btop',), 'ubuntu')
        self.plan = guard.PackagePlan((('btop', '1.4.6-2'),), ())
        transaction = patch('manage.package_transaction.package_transaction', side_effect=lambda **kw: nullcontext())
        transaction.start()
        self.addCleanup(transaction.stop)

    def test_preview_checks_context_policy_and_plan_before_scheduling(self):
        events = []
        with patch('manage.preflight.validate_local_context', side_effect=lambda: events.append('context')), \
             patch.object(guard, 'validate_request', side_effect=lambda r: events.append('request')), \
             patch('manage.package_policy.verify_effective_policy', side_effect=lambda **kw: events.append(('policy', kw))), \
             patch.object(guard, 'inspect_plan', side_effect=lambda r: events.append('plan') or self.plan), \
             patch('pyinfra.operations.server.shell') as shell:
            guard.install_packages(self.request)
        self.assertEqual(events, ['context', 'request', ('policy', {'preview': True}), 'plan'])
        self.assertTrue(shell.call_args.kwargs['_sudo'])
        self.assertIn('--apply btop', shell.call_args.kwargs['commands'])

    def test_matching_host_schedules_no_privileged_command(self):
        with patch('manage.preflight.validate_local_context'), patch.object(guard, 'validate_request'), \
             patch('manage.package_policy.verify_effective_policy'), \
             patch.object(guard, 'inspect_plan', return_value=guard.PackagePlan((), ())), \
             patch('pyinfra.operations.server.shell') as shell:
            guard.install_packages(self.request)
            shell.assert_not_called()

    def test_failed_policy_or_plan_never_schedules_install(self):
        for target in ('manage.package_policy.verify_effective_policy', 'manage.packages.inspect_plan'):
            with self.subTest(target=target), patch('manage.preflight.validate_local_context'), \
                 patch.object(guard, 'validate_request'), patch('manage.package_policy.verify_effective_policy'), \
                 patch.object(guard, 'inspect_plan', return_value=self.plan), \
                 patch(target, side_effect=RuntimeError('blocked')), patch('pyinfra.operations.server.shell') as shell:
                with self.assertRaisesRegex(RuntimeError, 'blocked'):
                    guard.install_packages(self.request)
                shell.assert_not_called()

    def test_apply_rechecks_effective_policy_and_plan_immediately_before_apt(self):
        events = []
        with patch.object(guard.os, 'geteuid', return_value=0), \
             patch.object(guard, 'validate_request', side_effect=lambda r: events.append('request')), \
             patch('manage.package_policy.verify_effective_policy', side_effect=lambda **kw: events.append(('policy', kw))), \
             patch.object(guard, 'inspect_plan', side_effect=lambda r: events.append('plan') or self.plan), \
             patch.object(guard.subprocess, 'run', side_effect=lambda *a, **kw: events.append(('apt', a, kw))):
            guard._apply_install(self.request)
        self.assertEqual(events[:3], ['request', ('policy', {}), 'plan'])
        self.assertEqual(events[3][1][0], ('/usr/bin/apt-get', '--no-install-recommends', '--no-remove', '--yes', 'install', 'btop'))
        self.assertTrue(events[3][2]['check'])
        self.assertEqual(events[3][2]['env'], {'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'LC_ALL': 'C', 'LANG': 'C'})

    def test_apply_failure_propagates_and_satisfied_apply_does_not_run_apt(self):
        with patch.object(guard.os, 'geteuid', return_value=0), patch.object(guard, 'validate_request'), \
             patch('manage.package_policy.verify_effective_policy'), \
             patch.object(guard, 'inspect_plan', return_value=self.plan) as planner, \
             patch.object(guard.subprocess, 'run', side_effect=subprocess.CalledProcessError(100, 'apt-get')) as run:
            with self.assertRaises(subprocess.CalledProcessError):
                guard._apply_install(self.request)
            planner.return_value = guard.PackagePlan((), ())
            run.reset_mock()
            guard._apply_install(self.request)
            run.assert_not_called()

    def test_suppression_preview_is_read_only_and_reports_intent(self):
        with patch('manage.preflight.validate_local_context'), patch.object(guard, 'validate_request'), \
             patch('manage.package_policy.verify_effective_policy'), \
             patch.object(guard, 'inspect_plan', return_value=self.plan), \
             patch('manage.package_transaction.inspect_service_policy') as inspect, \
             patch('pyinfra.operations.server.shell') as shell:
            guard.install_packages(self.request, prevent_service_start=True)
            inspect.assert_called_once_with()
            self.assertIn('--prevent-service-start', shell.call_args.kwargs['commands'])
            self.assertIn('service starts denied', shell.call_args.kwargs['name'])

    def test_unprivileged_internal_apply_is_rejected(self):
        with patch.object(guard.os, 'geteuid', return_value=1000), patch.object(guard.subprocess, 'run') as run:
            with self.assertRaisesRegex(RuntimeError, 'root'):
                guard._apply_install(self.request)
            run.assert_not_called()

    def test_real_pyinfra_preview_does_not_execute_privileged_helper(self):
        with tempfile.TemporaryDirectory() as temporary:
            deploy = Path(temporary) / 'preview.py'
            deploy.write_text('''from unittest.mock import patch
from manage.packages import PackageRequest, PackagePlan, install_packages
with patch('manage.packages.validate_request'), patch('manage.package_policy.verify_effective_policy'), patch('manage.packages.inspect_plan', return_value=PackagePlan((('btop', '1'),), ())):
    install_packages(PackageRequest(('btop',), 'ubuntu'))
''')
            result = subprocess.run([sys.executable, '-m', 'pyinfra', '@local', str(deploy), '--dry'],
                                    cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('Install reviewed native Ubuntu packages', result.stdout + result.stderr)

    def test_apt_manual_marker_only_accepts_an_already_satisfied_selection_once(self):
        satisfied = 'btop is already the newest version (1.4.6-2).\n'
        summary = '0 upgraded, 0 newly installed, 0 to remove and 0 not upgraded.\n'
        self.assertEqual(guard._parse_simulation(satisfied + 'btop set to manually installed.\n' + summary),
                         ({}, {'btop': ('btop', '1.4.6-2', None)}))
        for text in ('jq set to manually installed.\n',
                     'btop set to manually installed.\nbtop set to manually installed.\n',
                     'btop:amd64 set to manually installed.\n'):
            with self.subTest(text=text), self.assertRaises(RuntimeError):
                guard._parse_simulation(satisfied + text + summary)
