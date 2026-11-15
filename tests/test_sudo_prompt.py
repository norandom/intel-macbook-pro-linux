"""Exercise pyinfra's password flags against the installed sudo-rs diagnostic."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class SudoPromptTests(unittest.TestCase):
    def run_fixture(self, flag, patched=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sudo = root / 'sudo'
            sudo.write_text('''#!/usr/bin/python3
import os, subprocess, sys
args = sys.argv[1:]
if '-A' not in args:
    print('sudo: interactive authentication is required', file=sys.stderr)
    sys.exit(1)
password = subprocess.check_output([os.environ['SUDO_ASKPASS']], text=True).strip()
if password != 'fixture-private-password':
    sys.exit(1)
while args and args[0] in ('-H', '-A', '-k', '-n'):
    args.pop(0)
sys.exit(subprocess.call(args))
''')
            sudo.chmod(0o755)
            deploy = root / 'deploy.py'
            deploy.write_text(("import manage.preflight\n" if patched else "")
                              + "from pyinfra.operations import server\n"
                              "server.shell(commands='printf fixture-operation-ran', _sudo=True)\n")
            runner = root / 'runner.py'
            runner.write_text('''import sys
from unittest.mock import patch
from pyinfra_cli.cli import cli
with patch('pyinfra_cli.cli.getpass', return_value='fixture-private-password'), \
        patch('pyinfra.connectors.util.getpass', return_value='fixture-private-password'):
    cli.main(args=sys.argv[1:])
''')
            environment = dict(os.environ, PATH=str(root) + os.pathsep + os.environ['PATH'],
                               PYTHONPATH=str(Path(__file__).resolve().parents[1]))
            return subprocess.run([sys.executable, str(runner), '@local', str(deploy), flag, '-y'],
                                  env=environment, capture_output=True, text=True, timeout=30)

    def test_documented_flag_prompts_before_sudo_rs_retry_is_needed(self):
        result = self.run_fixture('--same-sudo-password')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('fixture-operation-ran', result.stdout + result.stderr)
        self.assertNotIn('fixture-private-password', result.stdout + result.stderr)

    def test_automatic_retry_misses_current_sudo_rs_prefix(self):
        result = self.run_fixture('--use-sudo-password')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('sudo: interactive authentication is required', result.stdout + result.stderr)

    def test_project_patch_lets_use_sudo_password_retry(self):
        result = self.run_fixture('--use-sudo-password', patched=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('fixture-operation-ran', result.stdout + result.stderr)
        self.assertNotIn('fixture-private-password', result.stdout + result.stderr)
