import re
import subprocess
import unittest
from pathlib import Path

from manage import cpu_mitigations as cm

ROOT = Path(__file__).resolve().parents[1]


class CpuMitigationsTests(unittest.TestCase):
    def test_dropin_appends_only_the_option(self):
        lines = [l for l in cm.dropin().splitlines() if not l.startswith("#")]
        self.assertEqual(lines, ['GRUB_CMDLINE_LINUX_DEFAULT="${GRUB_CMDLINE_LINUX_DEFAULT} mitigations=off"'])

    def test_dropin_keeps_existing_options_when_sourced(self):
        out = subprocess.run(["sh", "-c", "GRUB_CMDLINE_LINUX_DEFAULT='quiet splash pm_async=off'; . /dev/stdin; "
                              "echo \"$GRUB_CMDLINE_LINUX_DEFAULT\""], input=cm.dropin(), text=True,
                             capture_output=True, check=True).stdout.strip()
        self.assertEqual(out, "quiet splash pm_async=off mitigations=off")

    def test_dropin_lives_in_grub_d_not_main_file(self):
        self.assertTrue(cm.DROPIN.startswith("/etc/default/grub.d/") and cm.DROPIN.endswith(".cfg"))

    def _run(self, dropin: bool, main_has: bool, cfg_has: bool) -> str:
        import tempfile, os
        d = tempfile.mkdtemp()
        paths = {cm.BACKUP: f"{d}/backup", cm.DROPIN: f"{d}/dropin", "/etc/default/grub": f"{d}/grub",
                 cm.GRUB_CFG: f"{d}/grub.cfg"}  # longest first: grub.cfg is a prefix of the backup path
        cmd = cm.regenerate_commands()[0]
        for real, fake in paths.items():
            cmd = cmd.replace(real, fake)
        cmd = cmd.replace("update-grub", "echo REGENERATED")
        if dropin:
            open(paths[cm.DROPIN], "w").write(cm.dropin())
        open(paths["/etc/default/grub"], "w").write("GRUB_CMDLINE_LINUX_DEFAULT='quiet" + (" mitigations=off" if main_has else "") + "'\n")
        open(paths[cm.GRUB_CFG], "w").write("linux /vmlinuz root=x ro quiet" + (" mitigations=off" if cfg_has else "") + "\n")
        out = subprocess.run(["sh", "-c", cmd], capture_output=True, text=True, check=True).stdout
        if "REGENERATED" in out:
            self.assertTrue(os.path.exists(paths[cm.BACKUP]))
        return out

    def test_regenerates_only_on_mismatch_and_retries(self):
        self.assertIn("REGENERATED", self._run(dropin=True, main_has=False, cfg_has=False))   # new / failed before
        self.assertNotIn("REGENERATED", self._run(dropin=True, main_has=False, cfg_has=True))
        self.assertIn("REGENERATED", self._run(dropin=False, main_has=False, cfg_has=True))   # revert
        self.assertNotIn("REGENERATED", self._run(dropin=False, main_has=False, cfg_has=False))
        self.assertNotIn("REGENERATED", self._run(dropin=False, main_has=True, cfg_has=True))  # owner's own option

    def test_task_touches_nothing_else_in_the_boundary(self):
        task = (ROOT / "tasks/cpu_mitigations.py").read_text() + (ROOT / "manage/cpu_mitigations.py").read_text()
        for bad in ("update-initramfs", "grub-install", "cryptsetup", "crypttab", "fstab", "dkms",
                    "modprobe", "/boot/vmlinuz", "/etc/default/grub\"", "sed -i"):
            self.assertNotIn(bad, task)

    def test_notice_marker_has_no_regex_metacharacters(self):
        self.assertFalse(re.search(r"[()\[\]*+?|^$\\]", cm.NOTICE_MARKER.replace("{mark}", "")))

    def test_notice_is_valid_bash(self):
        subprocess.run(["bash", "-n"], input=cm.notice(), text=True, check=True)

    def test_in_deploy_order(self):
        self.assertIn('"cpu_mitigations"', (ROOT / "deploy.py").read_text())
