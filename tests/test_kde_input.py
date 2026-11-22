import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from manage import kde_input

ROOT = Path(__file__).resolve().parents[1]


def hypr_input():
    text = (ROOT / "files/desktop/hypr/input.conf").read_text()
    return {k: v.strip() for k, v in re.findall(r"^\s*(kb_layout|kb_variant|kb_options|repeat_rate|repeat_delay|numlock_by_default)\s*=\s*(.*)$", text, re.M)}


class KdeInputTests(unittest.TestCase):
    def test_same_as_hyprland(self):
        h = hypr_input()
        self.assertEqual(",".join(kde_input.LAYOUTS), h["kb_layout"])
        self.assertEqual(",".join(kde_input.VARIANTS), h["kb_variant"])
        self.assertEqual(",".join(kde_input.OPTIONS), h["kb_options"])
        self.assertEqual(str(kde_input.REPEAT_RATE), h["repeat_rate"])
        self.assertEqual(str(kde_input.REPEAT_DELAY), h["repeat_delay"])
        self.assertEqual(h["numlock_by_default"], "true")

    def test_apply_script_writes_only_when_different(self):
        script = kde_input.apply_script()
        subprocess.run(["bash", "-n"], input=script, text=True, check=True)
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, XDG_CONFIG_HOME=tmp, DBUS_SESSION_BUS_ADDRESS="unix:path=/nonexistent")
            if not Path("/usr/bin/kwriteconfig6").exists():
                self.skipTest("kwriteconfig6 required")
            first = subprocess.run(["bash", "-c", script], env=env, capture_output=True, text=True, check=True)
            self.assertIn("updated", first.stdout)
            kxkb = (Path(tmp) / "kxkbrc").read_text()
            self.assertIn("Options=compose:caps,shift:both_capslock_cancel,altwin:swap_ralt_rwin,lv3:lalt_switch", kxkb)
            self.assertIn("VariantList=mac_nodeadkeys,", kxkb)
            second = subprocess.run(["bash", "-c", script], env=env, capture_output=True, text=True, check=True)
            self.assertEqual(second.stdout, "")   # idempotent: nothing rewritten, no reload

    def test_task_wiring(self):
        self.assertIn("kde_input.apply_script()", (ROOT / "tasks/desktop.py").read_text())


if __name__ == "__main__":
    unittest.main()
