"""CAKE traffic shaper: settings, helper script and wiring (offline, no root)."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from manage import traffic_shaping as ts

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "files/traffic-shaping"


class Settings(unittest.TestCase):
    def test_rates_convert_to_kbit_and_zero_means_off(self):
        self.assertEqual(ts.kbit(None, "k"), 0)
        self.assertEqual(ts.kbit(0, "k"), 0)
        self.assertEqual(ts.kbit(35, "k"), 35000)
        self.assertEqual(ts.kbit(7.5, "k"), 7500)

    def test_invalid_rates_are_rejected(self):
        for bad in (True, "35", -1, 0.5, ts.MAX_MBIT + 1):
            with self.assertRaises(ValueError, msg=repr(bad)):
                ts.kbit(bad, "cake_upload_mbit")

    def test_conf_is_what_the_helper_parses(self):
        with tempfile.TemporaryDirectory() as d:
            conf = Path(d, "cake.conf")
            conf.write_text(ts.conf(35000, 100000))
            env = dict(os.environ, T2_CAKE_CONF=str(conf), T2_CAKE_DEVICES="lo")
            out = subprocess.run(["sh", str(SRC / "t2-cake"), "status"], env=env, capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertIn("upload 35000 kbit/s, download 100000 kbit/s", out.stdout)
            conf.write_text("UP_KBIT=$(reboot)\nDOWN_KBIT=12 34\n")     # never evaluated, never trusted
            out = subprocess.run(["sh", str(SRC / "t2-cake"), "status"], env=env, capture_output=True, text=True)
            self.assertIn("upload 0 kbit/s, download 0 kbit/s", out.stdout)


class Wiring(unittest.TestCase):
    def test_helper_syntax_and_usage(self):
        self.assertEqual(subprocess.run(["sh", "-n", str(SRC / "t2-cake")]).returncode, 0)
        self.assertEqual(subprocess.run(["sh", str(SRC / "t2-cake")], capture_output=True).returncode, 2)

    def test_tunnel_is_shaped_below_the_uplink(self):
        text = (SRC / "t2-cake").read_text()
        self.assertIn("TUNNEL_PCT=92", text)
        self.assertIn("tailscale0) echo $(($2 * TUNNEL_PCT / 100))", text)
        self.assertIn('cake bandwidth "$(rate "$dev" "$DOWN_KBIT")kbit" ingress', text)

    def test_unit_rule_and_deploy_point_at_the_helper(self):
        unit = (SRC / "t2-cake.service").read_text()
        self.assertIn(f"ExecStart={ts.HELPER} apply", unit)
        self.assertIn(f"ExecStop={ts.HELPER} clear", unit)
        rule = (SRC / "90-t2-cake.rules").read_text()
        self.assertIn(f'RUN+="{ts.HELPER} apply $name"', rule)
        self.assertIn('"traffic_shaping"', (ROOT / "deploy.py").read_text())
        task = (ROOT / "tasks/traffic_shaping.py").read_text()
        self.assertNotIn("sysctl", task.split('"""')[2])   # runtime qdiscs only


if __name__ == "__main__":
    unittest.main()
