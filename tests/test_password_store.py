import unittest
from manage import password_store as ps

ENTRY = "[Desktop Entry]\nName=V\nExec=/usr/bin/vivaldi-stable %U\n[Desktop Action new]\nExec=/usr/bin/vivaldi-stable --new-window\n"


class PasswordStoreTests(unittest.TestCase):
    def test_flag_added_to_every_exec_once(self):
        out = ps.override(ENTRY, "kwallet6")
        execs = [l for l in out.splitlines() if l.startswith("Exec=")]
        self.assertEqual(execs, ["Exec=/usr/bin/vivaldi-stable --password-store=kwallet6 %U",
                                 "Exec=/usr/bin/vivaldi-stable --password-store=kwallet6 --new-window"])
        self.assertEqual(ps.override(out, "kwallet6").count("--password-store"), 2)  # idempotent


if __name__ == "__main__":
    unittest.main()
