import re
import subprocess
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

    def test_hibernate_mode_shutdown_not_platform(self):
        conf = (ROOT / "files/desktop/systemd-sleep/t2-hibernate.conf").read_text()
        self.assertIn("[Sleep]\nHibernateMode=shutdown\n", conf)
        task = (ROOT / "tasks/desktop.py").read_text()
        self.assertIn('dest="/etc/systemd/sleep.conf.d/t2-hibernate.conf"', task)
        self.assertIn('path="/etc/systemd/sleep.conf.d/t2-hibernate.conf", present=False', task)
        self.assertNotIn("rmmod", task)          # the task itself never unloads anything

    def test_lid_hibernate_needs_hibernate_and_never_restarts_logind(self):
        task = (ROOT / "tasks/desktop.py").read_text()
        self.assertIn('setting("lid_close", "suspend")', task)
        self.assertIn('if lid_close == "hibernate" and not hibernate:', task)
        self.assertIn("HandleLidSwitch=hibernate", task)
        self.assertIn("systemctl kill -s HUP --kill-whom=main systemd-logind.service", task)
        self.assertNotIn("restart systemd-logind", task)

    def test_t2_driver_hook_is_hibernate_only_and_never_forces(self):
        hook = (ROOT / "files/desktop/t2-hibernate-bce").read_text()
        unit = (ROOT / "files/desktop/systemd-system/t2-hibernate-bce.service").read_text()
        self.assertNotIn("rmmod", hook)
        self.assertNotIn("-f ", hook.replace("rm -f", ""))
        self.assertIn("modprobe -r t2bce_audio t2bce_vhci t2bce_core t2bce_dma", hook)
        self.assertIn("hibernate cancelled", hook)            # unload failure -> exit 1
        self.assertIn("exit 1", hook)
        for svc in ("systemd-hibernate.service", "systemd-hybrid-sleep.service", "systemd-suspend-then-hibernate.service"):
            self.assertIn(svc, unit.split("RequiredBy=")[1])
        self.assertNotIn("systemd-suspend.service", unit)
        self.assertIn("systemctl suspend", hook)        # cancelled hibernate falls back to suspend
        self.assertIn("runuser -u", hook)
        self.assertIn("Before=systemd-hibernate.service", unit)
        self.assertIn("StopWhenUnneeded=yes", unit)
        subprocess.run(["sh", "-n", str(ROOT / "files/desktop/t2-hibernate-bce")], check=True)

    def test_hook_only_installed_with_hibernate(self):
        task = (ROOT / "tasks/desktop.py").read_text()
        block = task[task.index('if hibernate:'):task.index('lid_close = setting')]
        on, off = block.split("\nelse:", 1)
        self.assertIn("t2-hibernate-bce", on)
        self.assertIn("systemctl disable t2-hibernate-bce.service", off)

    def test_rule_sorts_before_ubuntus(self):
        self.assertLess("49-t2-hibernate.rules", "com.ubuntu.desktop.rules")

    def test_guard_checks_disk_swap_not_zram(self):
        script = (ROOT / "files/desktop/bin/hypr-hibernate").read_text()
        self.assertIn("zram", script)
        self.assertIn("MemAvailable", script)
        self.assertIn("systemctl hibernate 2>&1", script)
        self.assertIn("Hibernate refused", script)  # a refusal is shown, never silent

    def test_off_by_default_and_removable(self):
        task = (ROOT / "tasks/desktop.py").read_text()
        self.assertIn('setting("hibernate", False)', task)
        self.assertIn('path="/etc/polkit-1/rules.d/49-t2-hibernate.rules", present=False', task)

    def test_never_touches_swap_or_resume(self):
        task = (ROOT / "tasks/desktop.py").read_text()
        for bad in ("mkswap", "swapon", "swapoff", "resume=", "update-initramfs", "lvextend", "lvreduce"):
            self.assertNotIn(bad, task)
