import unittest
from pathlib import Path

from manage import own_titlebar

ROOT = Path(__file__).resolve().parents[1]


class OwnTitlebarTests(unittest.TestCase):
    def test_rules(self):
        self.assertEqual(own_titlebar.conf(["Deckle"]), "windowrule = match:class ^(Deckle)$, hyprbars:no_bar on\n")
        self.assertIn(r"^(com\.example\.fim)$", own_titlebar.conf(["com.example.fim"]))
        self.assertEqual(own_titlebar.conf([]), "")
        for bad in ("Deckle", ["De ckle"], ["a)|.*("], [1]):
            with self.subTest(bad=bad), self.assertRaises(RuntimeError):
                own_titlebar.conf(bad)

    def test_wiring(self):
        self.assertIn("source = ~/.config/hypr/apps.conf", (ROOT / "files/desktop/hypr/hyprland.conf").read_text())
        self.assertIn('setting("own_titlebar_apps", [])', (ROOT / "tasks/desktop.py").read_text())
        self.assertIn("# own_titlebar_apps = []", (ROOT / "files/config.example.toml").read_text())


if __name__ == "__main__":
    unittest.main()
