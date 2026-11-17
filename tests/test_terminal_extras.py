"""Behavior checks for local-only history and terminal integration assets."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TerminalExtrasTests(unittest.TestCase):
    def test_local_history_policy(self):
        policy = tomllib.loads((ROOT / 'files/shell/atuin.toml').read_text())
        self.assertFalse(policy['auto_sync'])
        self.assertFalse(policy['update_check'])
        self.assertEqual(policy['sync_address'], 'http://127.0.0.1:9')
        self.assertFalse(policy['daemon']['enabled'])
    @unittest.skipUnless(shutil.which('fish'), 'fish unavailable')
    def test_fish_overrides_inherited_network_settings_before_atuin_init(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stub = root / 'atuin'
            stub.write_text('#!/usr/bin/python3\nimport os, json, sys\n'
                'open(os.environ["RESULT"], "w").write(json.dumps({"args":sys.argv[1:], '
                '"auto":os.environ.get("ATUIN_AUTO_SYNC"), '
                '"update":os.environ.get("ATUIN_UPDATE_CHECK"), '
                '"address":os.environ.get("ATUIN_SYNC_ADDRESS"), '
                '"daemon":os.environ.get("ATUIN_DAEMON__ENABLED")}))\n')
            stub.chmod(0o755)
            env = dict(os.environ, PATH=f'{root}:/usr/bin:/bin', RESULT=str(root/'result'),
                       ATUIN_AUTO_SYNC='true', ATUIN_UPDATE_CHECK='true',
                       ATUIN_SYNC_ADDRESS='https://api.atuin.sh', ATUIN_DAEMON__ENABLED='true')
            subprocess.run(['fish', '--no-config', '-c',
                            'source "$argv[1]"', str(ROOT/'files/shell/navigation.fish')],
                           env=env, check=True, capture_output=True)
            result = json.loads((root/'result').read_text())
            self.assertEqual(result, {'args':['init', 'fish', '--disable-up-arrow'],
                'auto':'false', 'update':'false', 'address':'http://127.0.0.1:9', 'daemon':'false'})

    def test_rdp_restriction_does_not_restrict_ssh(self):
        firewall = (ROOT/'files/remote-access/rdp-tailscale-only.nft').read_text()
        self.assertIn('iifname { "lo", "tailscale0" } tcp dport 3389 accept', firewall)
        self.assertIn('tcp dport 3389 drop', firewall)
        self.assertNotIn('dport 22', firewall)
