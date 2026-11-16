import subprocess
import unittest
from pathlib import Path

from manage import security_keys as sk

ROOT = Path(__file__).resolve().parents[1]


class SecurityKeyTests(unittest.TestCase):
    def test_profile_is_a_primary_alternative_like_fprintd(self):
        p = sk.profile()
        self.assertIn("Default: no\n", p)
        self.assertIn("Auth-Type: Primary\n", p)
        self.assertIn("Priority: 260\n", p)          # before pam_unix (256), like fprintd
        auth = [l for l in p.splitlines() if l.startswith("\t")]
        self.assertEqual(len(auth), 2)
        self.assertTrue(auth[0].startswith("\t[success=1 default=ignore]\tpam_succeed_if.so quiet service notin "))
        self.assertTrue(auth[1].startswith("\t[success=end default=ignore]\tpam_u2f.so "))
        for opt in ("nouserok", "cue", f"authfile={sk.MAPPINGS}", f"origin={sk.ORIGIN}"):
            self.assertIn(opt, auth[1])
        self.assertNotIn("required", p)
        self.assertNotIn("requisite", p)

    def test_only_interactive_local_services(self):
        self.assertNotIn("sshd", sk.SERVICES)
        self.assertNotIn("cron", sk.SERVICES)
        self.assertIn("sudo", sk.SERVICES)
        self.assertIn("hyprlock", sk.SERVICES)

    def test_mapping_lines_keep_only_this_user(self):
        text = "mc:AAAAkeyhandle1,BBBBpub1,es256,+presence:CCCCkey2,DDDDpub2,es256,+presence\nroot:xyz,abc\n\n"
        lines = sk.mapping_lines(text, "mc")
        self.assertEqual(len(lines), 1)
        self.assertEqual(sk.key_count(lines[0]), 2)
        self.assertEqual(sk.mapping_lines("garbage\n", "mc"), [])

    def test_origin_matches_helper(self):
        helper = (ROOT / "files/security-keys/t2-yubikey").read_text()
        self.assertIn(f'origin="{sk.ORIGIN}"', helper)
        subprocess.run(["bash", "-n", str(ROOT / "files/security-keys/t2-yubikey")], check=True)

    def test_task_never_touches_pam_files_directly(self):
        task = (ROOT / "tasks/security_keys.py").read_text()
        self.assertNotIn('dest="/etc/pam.d', task)
        self.assertNotIn("sed -i", task)
        self.assertIn("pam-auth-update --enable", task)
