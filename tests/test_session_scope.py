import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from manage import session_scope as scope

ROOT = Path(__file__).resolve().parents[1]


class SessionScopeTests(unittest.TestCase):
    def test_hyprland_only_dropin(self):
        text = scope.hyprland_only_dropin("Managed")
        self.assertIn("[Unit]\nConditionEnvironment=XDG_CURRENT_DESKTOP=Hyprland\n", text)
        self.assertEqual(set(scope.HYPRLAND_ONLY),
                         {"waybar.service", "mako.service", "hypridle.service", "hyprpolkitagent.service"})

    def test_kde_scale_and_width(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "kwinoutputconfig.json"
            p.write_text(json.dumps([{"name": "outputs", "data": [{"connectorName": "eDP-1", "scale": 1.5}]}]))
            self.assertEqual(scope.kde_scale(p), 1.5)
            self.assertIsNone(scope.kde_scale(Path(tmp) / "missing.json"))
            p.write_text("{not json")
            self.assertIsNone(scope.kde_scale(p))
        self.assertEqual(scope.kde_strip_width(15, "1.6", 1.5), 16)   # 24 physical px either way
        self.assertEqual(scope.kde_strip_width(15, "auto", 1.5), 15)
        self.assertEqual(scope.kde_strip_width(15, "1.6", None), 15)

    def test_kde_strip_files(self):
        bar = json.loads(scope.kde_strip_config("Managed", 16).split("\n", 1)[1])
        self.assertEqual((bar["output"], bar["position"], bar["width"], bar["exclusive"], bar["name"]),
                         ("eDP-1", "left", 16, True, "leftstrip"))   # style.css: window#waybar.leftstrip = black
        unit = scope.kde_strip_unit("Managed")
        self.assertIn("ConditionEnvironment=XDG_CURRENT_DESKTOP=KDE\n", unit)
        self.assertIn("WantedBy=graphical-session.target\n", unit)
        self.assertIn("window#waybar.leftstrip { background: #000000;", (ROOT / "files/desktop/waybar/style.css").read_text())

    @unittest.skipUnless(Path("/usr/bin/systemd-analyze").exists(), "systemd-analyze required")
    def test_unit_verifies(self):
        with tempfile.TemporaryDirectory() as tmp:
            unit = Path(tmp) / scope.KDE_STRIP_UNIT
            unit.write_text(scope.kde_strip_unit("Managed").replace("%h", tmp))
            r = subprocess.run(["systemd-analyze", "--user", "verify", str(unit)], capture_output=True, text=True)
            ours = [l for l in (r.stderr + r.stdout).splitlines() if scope.KDE_STRIP_UNIT in l]
            self.assertEqual(ours, [])

    def test_task_wiring(self):
        task = (ROOT / "tasks/desktop.py").read_text()
        self.assertIn("session_scope.HYPRLAND_ONLY", task)
        self.assertIn("systemctl --user enable {session_scope.KDE_STRIP_UNIT}", task)


if __name__ == "__main__":
    unittest.main()
