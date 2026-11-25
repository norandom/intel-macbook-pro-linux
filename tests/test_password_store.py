import unittest
from pathlib import Path
from manage import password_store as ps

ENTRY = "[Desktop Entry]\nName=V\nExec=/usr/bin/vivaldi-stable %U\n[Desktop Action new]\nExec=/usr/bin/vivaldi-stable --new-window\n"


class PasswordStoreTests(unittest.TestCase):
    def test_flag_added_to_every_exec_once(self):
        out = ps.override(ENTRY, "kwallet6")
        execs = [l for l in out.splitlines() if l.startswith("Exec=")]
        self.assertEqual(execs, ["Exec=/usr/bin/vivaldi-stable --password-store=kwallet6 %U",
                                 "Exec=/usr/bin/vivaldi-stable --password-store=kwallet6 --new-window"])
        self.assertEqual(ps.override(out, "kwallet6").count("--password-store"), 2)  # idempotent

    def test_browsers_get_vaapi_flags_once_even_without_store(self):
        out = ps.override(ENTRY, "", ps.VIDEO_FLAGS)
        self.assertNotIn("--password-store", out)
        self.assertEqual(out.count("--enable-features=AcceleratedVideoDecodeLinuxGL"), 2)
        self.assertEqual(ps.override(out, "kwallet6", ps.VIDEO_FLAGS).count("--enable-features="), 2)
        self.assertIn("vivaldi-stable.desktop", ps.VIDEO_APPS)

    def test_youtube_av1_policy_for_both_browsers(self):
        self.assertEqual(ps.POLICY["ExtensionInstallForcelist"],
                         ["omkfmpieigblcllmkgbflkikinpkodlk;https://clients2.google.com/service/update2/crx"])
        self.assertIn("/etc/vivaldi/policies/managed", ps.POLICY_DIRS)

    def test_kde_menu_cache_rebuilt_when_entries_change(self):
        task = (Path(__file__).resolve().parents[1] / "tasks/desktop.py").read_text()
        self.assertIn('commands=["kbuildsycoca6 >/dev/null 2>&1 || true"]', task)
        self.assertIn("_if=any_changed(*entry_ops)", task)


if __name__ == "__main__":
    unittest.main()
