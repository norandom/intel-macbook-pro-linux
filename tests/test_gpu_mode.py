import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class GpuModeTests(unittest.TestCase):
    def setUp(self):
        self.task = (ROOT / "tasks/desktop.py").read_text()
        self.tool = ROOT / "files/desktop/bin/hypr-gpu"

    def test_both_sessions_use_the_same_mode_file(self):
        self.assertIn('gpu_env("AQ_DRM_DEVICES")', self.task)
        self.assertIn('gpu_env("KWIN_DRM_DEVICES")', self.task)
        self.assertIn('f"{cfg}/plasma-workspace/env/t2-gpu.sh"', self.task)
        self.assertIn('f"{cfg}/uwsm/env-hyprland"', self.task)

    def test_battery_is_intel_only_and_external_adds_amd(self):
        fn = self.task.split("def gpu_env(var):")[1].split("\n\n\n")[0]
        self.assertIn("external) if [ -e /dev/dri/amd-dgpu ]; then export {var}=/dev/dri/intel-igpu:/dev/dri/amd-dgpu", fn)
        self.assertIn("*) export {var}=/dev/dri/intel-igpu ;;", fn)
        self.assertIn("if [ -e /dev/dri/intel-igpu ]", fn)   # missing udev names never blank a session

    def test_tool_reports_and_logs_out_both_sessions(self):
        tool = self.tool.read_text()
        self.assertIn("running '^/usr/bin/kwin_wayland_wrapper' KWIN_DRM_DEVICES", tool)
        self.assertIn("running '(^|/)Hyprland( |$)' AQ_DRM_DEVICES", tool)
        self.assertIn("org.kde.Shutdown /Shutdown org.kde.Shutdown.logout", tool)
        subprocess.run(["bash", "-n", str(self.tool)], check=True)


if __name__ == "__main__":
    unittest.main()
