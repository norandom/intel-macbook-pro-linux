"""Fixture tests for laptop-resource-policy helpers and static assets (no host mutation)."""
import re
import shlex
import unittest
from pathlib import Path

from manage import resource_policy as rp

ROOT = Path(__file__).resolve().parents[1]
FILES = ROOT / "files/resource-policy"


class TurboTests(unittest.TestCase):
    def test_tmpfiles_rule_exact(self):
        self.assertEqual((FILES / "no-turbo.conf").read_text(),
                         "w /sys/devices/system/cpu/intel_pstate/no_turbo - - - - 1\n")

    def test_alias_fragment_exact_and_side_effect_free(self):
        lines = (FILES / "turbo.bash").read_text().splitlines()
        self.assertEqual(lines, [
            "alias turbo-on='echo 0 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo'",
            "alias turbo-off='echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo'",
            "alias turbo-status='cat /sys/devices/system/cpu/intel_pstate/no_turbo'",
        ])
        self.assertEqual(rp.TURBO_FRAGMENT, "~/.config/t2-mac-kde/turbo.bash")


class ZramTests(unittest.TestCase):
    def test_capped_lz4_above_disk_swap(self):
        text = (FILES / "zram-generator.conf").read_text()
        self.assertIn("zram-size = min(ram / 2, 4096)", text)
        self.assertIn("compression-algorithm = lz4", text)
        self.assertIn("swap-priority = 100", text)

    def test_task_never_tears_down_swap_or_touches_boot(self):
        task = (ROOT / "tasks/resource_policy.py").read_text()
        for forbidden in ("swapoff", "mkswap", "restart systemd-zram", "fstab", "update-grub",
                          "update-initramfs", "modprobe", "sysctl --system", "nvidia", "amdgpu"):
            self.assertNotIn(forbidden, task)


class EarlyoomTests(unittest.TestCase):
    def avoid(self):
        line = [l for l in rp.earlyoom_defaults().splitlines() if l.startswith("EARLYOOM_ARGS=")][0]
        args = shlex.split(shlex.split(line.split("=", 1)[1])[0])
        self.assertEqual(args[:6], ["-m", "5", "-s", "10", "-r", "3600"])
        self.assertNotIn("--prefer", args)
        return re.compile(args[args.index("--avoid") + 1])

    def test_avoids_both_desktop_stacks(self):
        pattern = self.avoid()
        for comm in ("plasmashell", "kwin_wayland", "ksmserver", "kded6", "startplasma-way",
                     "Hyprland", "waybar", "pipewire", "wireplumber", "sddm", "Xwayland"):
            self.assertTrue(pattern.search(comm), comm)
        for comm in ("firefox", "code", "plasmashellx", "kded"):
            self.assertFalse(pattern.search(comm), comm)

    def test_comm_names_fit_kernel_limit(self):
        self.assertTrue(all(len(c) <= 15 for c in rp.AVOID_COMMS))
        with self.assertRaises(ValueError):
            rp.avoid_regex(("startplasma-wayland",))


class LimitTests(unittest.TestCase):
    def test_inotify_floor_never_lowers(self):
        self.assertEqual(rp.inotify_instances_target(128), 1024)
        self.assertEqual(rp.inotify_instances_target(8192), 8192)
        self.assertEqual(rp.inotify_instances_target(None), 1024)
        self.assertIn("fs.inotify.max_user_instances = 1024", rp.limits_sysctl(128))

    def test_coredump_only_for_systemd_handler(self):
        self.assertTrue(rp.coredump_applicable("|/usr/lib/systemd/systemd-coredump %P %u"))
        self.assertFalse(rp.coredump_applicable("|/usr/share/apport/apport -p%p"))
        self.assertFalse(rp.coredump_applicable("core"))

    def test_diagnostic_limits(self):
        self.assertIn("SystemMaxUse=500M", (FILES / "journald.conf").read_text())
        self.assertIn("RuntimeMaxUse=100M", (FILES / "journald.conf").read_text())
        self.assertIn("MaxUse=500M", (FILES / "coredump.conf").read_text())
        self.assertIn("KeepFree=1G", (FILES / "coredump.conf").read_text())

    def test_unit_installed(self):
        self.assertFalse(rp.unit_installed(""))
        self.assertFalse(rp.unit_installed("not-found"))
        self.assertTrue(rp.unit_installed("enabled"))
        self.assertTrue(rp.unit_installed("masked"))


if __name__ == "__main__":
    unittest.main()
