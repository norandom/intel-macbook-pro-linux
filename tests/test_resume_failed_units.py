import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ResumeFailedUnitTests(unittest.TestCase):
    def test_fan_curve_watchdog_survives_suspend_entry(self):
        unit = (ROOT / "files/resource-policy/t2-fan-curve.service").read_text()
        self.assertIn("\nWatchdogSec=60\n", unit)

    def test_crash_notifier_skips_upload_while_whoopsie_masked(self):
        stub = ROOT / "files/desktop/kubuntu-notification-helper/whoopsie-upload-all"
        text = stub.read_text()
        self.assertIn("Managed by t2-mac-kde (desktop)", text)
        self.assertIn('UnitFileState whoopsie.service 2>/dev/null)" = masked', text)
        self.assertIn("exec /usr/share/kubuntu-notification-helper/whoopsie-upload-all", text)
        self.assertTrue(os.access(stub, os.X_OK))
        self.assertIn(".local/share/kubuntu-notification-helper/whoopsie-upload-all",
                      (ROOT / "tasks/desktop.py").read_text())
        subprocess.run(["sh", "-n", str(stub)], check=True)


if __name__ == "__main__":
    unittest.main()
