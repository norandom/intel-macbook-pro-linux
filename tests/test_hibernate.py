import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class HibernateTests(unittest.TestCase):
    def test_polkit_rule_only_for_active_local_hibernate(self):
        rule = (ROOT / "files/desktop/polkit/49-t2-hibernate.rules").read_text()
        self.assertIn("subject.active && subject.local", rule)
        self.assertEqual(set(re.findall(r'action\.id == "([^"]+)"', rule)),
                         {"org.freedesktop.login1.hibernate", "org.freedesktop.login1.handle-hibernate-key",
                          "org.freedesktop.upower.hibernate"})
        self.assertNotIn("multiple-sessions", rule)
        self.assertNotIn("suspend", rule.split("*/")[-1].split("polkit.addRule")[1])

    def test_rule_sorts_before_ubuntus(self):
        self.assertLess("49-t2-hibernate.rules", "com.ubuntu.desktop.rules")

    def test_guard_checks_disk_swap_not_zram(self):
        script = (ROOT / "files/desktop/bin/hypr-hibernate").read_text()
        self.assertIn("zram", script)
        self.assertIn("MemAvailable", script)
        self.assertIn("exec systemctl hibernate", script)

    def test_off_by_default_and_removable(self):
        task = (ROOT / "tasks/desktop.py").read_text()
        self.assertIn('setting("hibernate", False)', task)
        self.assertIn('path="/etc/polkit-1/rules.d/49-t2-hibernate.rules", present=False', task)

    def test_never_touches_swap_or_resume(self):
        task = (ROOT / "tasks/desktop.py").read_text()
        for bad in ("mkswap", "swapon", "swapoff", "resume=", "update-initramfs", "lvextend", "lvreduce"):
            self.assertNotIn(bad, task)
