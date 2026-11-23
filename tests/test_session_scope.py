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

    def test_kde_strip_unit_and_helper(self):
        unit = scope.kde_strip_unit("Managed", 16)
        self.assertIn("ExecStart=%h/.local/bin/t2-leftstrip 16 eDP-1\n", unit)
        self.assertIn("ConditionEnvironment=XDG_CURRENT_DESKTOP=KDE\n", unit)
        self.assertIn("WantedBy=graphical-session.target\n", unit)
        helper = (ROOT / "files/desktop/bin/t2-leftstrip").read_text()
        self.assertIn("Managed by t2-mac-kde (desktop)", helper)           # owned_put marker
        self.assertIn("set_exclusive_zone(win, -1)", helper)              # drawn over the Plasma panel
        self.assertIn("GtkLayerShell.Layer.OVERLAY", helper)
        self.assertIn("p.location == 'left' && p.widgetIds.length == 0", helper)   # only our empty panel
        self.assertIn("(p.location == 'bottom' || p.location == 'top') && p.lengthMode == 'fill'", helper)  # only an untouched panel, also a theme's top panel
        self.assertIn('sys.argv[1:2] == ["--panel"]', helper)   # leftbar: panels again after a theme change
        self.assertIn('"t2-leftstrip"', (ROOT / "tasks/desktop.py").read_text())
        subprocess.run(["python3", "-m", "py_compile", str(ROOT / "files/desktop/bin/t2-leftstrip")], check=True)

    @unittest.skipUnless(Path("/usr/bin/systemd-analyze").exists(), "systemd-analyze required")
    def test_unit_verifies(self):
        with tempfile.TemporaryDirectory() as tmp:
            unit = Path(tmp) / scope.KDE_STRIP_UNIT
            unit.write_text(scope.kde_strip_unit("Managed", 16).replace("%h", tmp))
            helper = Path(tmp) / ".local/bin/t2-leftstrip"
            helper.parent.mkdir(parents=True)
            helper.write_text("#!/bin/sh\n")
            helper.chmod(0o755)
            r = subprocess.run(["systemd-analyze", "--user", "verify", str(unit)], capture_output=True, text=True)
            ours = [l for l in (r.stderr + r.stdout).splitlines() if scope.KDE_STRIP_UNIT in l]
            self.assertEqual(ours, [])

    def test_easyeffects_in_both_sessions(self):
        unit = (ROOT / "files/audio-effects/easyeffects.service").read_text()
        self.assertIn("WantedBy=hypr-desktop.target plasma-workspace.target", unit)
        self.assertIn("systemctl --user reenable easyeffects.service", (ROOT / "tasks/audio_effects.py").read_text())

    def test_kde_brightness_keys(self):
        entry = scope.brightness_entry("Managed", "/home/u", "-5", "Down")
        self.assertIn("Exec=/home/u/.local/bin/hypr-brightness screen -5\n", entry)
        self.assertIn("NoDisplay=true\n", entry)
        self.assertIn("StartupNotify=false\n", entry)         # no bouncing icon on each key press
        unit = scope.kde_keys_unit("Managed")
        self.assertIn("ConditionEnvironment=XDG_CURRENT_DESKTOP=KDE\n", unit)
        self.assertIn("ExecStart=%h/.local/bin/t2-kde-keys\n", unit)
        self.assertIn("WantedBy=plasma-workspace.target\n", unit)
        helper = (ROOT / "files/desktop/bin/t2-kde-keys").read_text()
        self.assertIn("0x10000B3", helper)                      # Qt::Key_MonBrightnessDown
        self.assertIn('"Decrease Screen Brightness"', helper)   # PowerDevil's plain key unbound
        self.assertNotIn("Small", helper)                       # Shift = 1 % steps stays PowerDevil's
        osd = (ROOT / "files/desktop/bin/hypr-osd").read_text()
        self.assertIn("org.kde.osdService.brightnessChanged", osd)
        subprocess.run(["python3", "-m", "py_compile", str(ROOT / "files/desktop/bin/t2-kde-keys")], check=True)

    def test_task_wiring(self):
        task = (ROOT / "tasks/desktop.py").read_text()
        self.assertIn("session_scope.HYPRLAND_ONLY", task)
        self.assertIn("systemctl --user enable {session_scope.KDE_STRIP_UNIT}", task)


if __name__ == "__main__":
    unittest.main()


class StatsWidgetTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1] / "files/desktop/plasma/net.local.t2stats"

    def test_plasmoid_package(self):
        import json
        meta = json.loads((self.ROOT / "metadata.json").read_text())
        self.assertEqual(meta["KPlugin"]["Id"], "net.local.t2stats")
        self.assertIn("Managed by t2-mac-kde (desktop)", meta["X-Managed-By"])
        qml = (self.ROOT / "contents/ui/main.qml").read_text()
        self.assertIn("Managed by t2-mac-kde (desktop)", qml)
        self.assertIn('name="mode"', (self.ROOT / "contents/config/main.xml").read_text())
        for sensor in ("network/all/upload", "network/all/download", "cpu/all/usage",
                       "memory/physical/usedPercent", "cpu/all/maximumTemperature"):
            self.assertIn(sensor, qml)
        self.assertNotRegex(qml, r"function (short|int|char|byte|long|float|double)\(")  # reserved in QML JS
        # temperature colours = hypr-thermal's thresholds
        thermal = (self.ROOT.parents[1] / "bin/hypr-thermal").read_text()
        self.assertIn("-ge 85 ] && class=warning", thermal)
        self.assertIn("-ge 95 ] && class=critical", thermal)
        self.assertIn('t >= 95 ? "#c0605a" : t >= 85 ? "#a87a2f"', qml)
        self.assertIn("net.local.t2stats", (self.ROOT.parents[3] / "tasks/desktop.py").read_text())
