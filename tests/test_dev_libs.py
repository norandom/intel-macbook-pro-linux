"""Dev libraries task and the guard's named replacements (offline except the apt simulation)."""
import shutil
import unittest
from pathlib import Path
from unittest import mock

from manage import applications, packages as guard
from manage.packages import PackageRequest

ROOT = Path(__file__).resolve().parents[1]
SIM = """Remv libappindicator3-dev [12.10.1]
Remv libappindicator3-1 [12.10.1] [slack-desktop:amd64 ]
Inst libayatana-appindicator3-1 (0.5.94-1build1 Ubuntu:26.04/resolute [amd64])
"""


class ReplacesTests(unittest.TestCase):
    def test_only_named_removals_pass(self):
        plan = guard._parse_simulation(SIM, ("libappindicator3-dev", "libappindicator3-1"))
        self.assertEqual(plan.removals, ("libappindicator3-dev", "libappindicator3-1"))
        with self.assertRaisesRegex(RuntimeError, "libappindicator3-1"):
            guard._parse_simulation(SIM, ("libappindicator3-dev",))
        with self.assertRaisesRegex(RuntimeError, "blocked"):
            guard._parse_simulation(SIM)

    def test_replaces_are_validated(self):
        for bad in (("linux-image-generic",), ("cryptsetup",), ("pkg-config",), ("foo-",), ("a=1",)):
            with self.subTest(bad=bad), self.assertRaises(RuntimeError):
                guard.validate_request(PackageRequest(packages=("pkg-config",), replaces=bad))

    def test_no_remove_stays_unless_a_replaced_package_is_installed(self):
        request = PackageRequest(packages=("libayatana-appindicator3-dev",), replaces=("libappindicator3-dev",))
        with mock.patch.object(guard, "_installed", return_value=False):
            self.assertIn("--no-remove", guard._apt_args(request))
        with mock.patch.object(guard, "_installed", return_value=True):
            argv = guard._apt_args(request)
            self.assertNotIn("--no-remove", argv)
            self.assertEqual(argv[-1], "libappindicator3-dev-")
        self.assertIn("--no-remove", guard._apt_args(PackageRequest(packages=("pkg-config",))))

    @unittest.skipUnless(shutil.which("apt-get"), "apt required")
    def test_live_plan_passes_the_guard(self):
        from manage.packages import inspect_plan
        source = (ROOT / "tasks/dev_libs.py").read_text()
        scope = {}
        exec(source.split("validate_local_context()")[0].split('"""', 2)[2]
             .replace("from manage.preflight import validate_local_context\n", "")
             .replace("from manage.userconfig import setting\n", ""), scope)
        plan = inspect_plan(PackageRequest(packages=scope["PACKAGES"], replaces=scope["REPLACES"]))
        self.assertTrue(set(plan.removals) <= set(scope["REPLACES"]))


class DevLibsTaskTests(unittest.TestCase):
    def test_task(self):
        task = (ROOT / "tasks/dev_libs.py").read_text()
        self.assertIn('"libayatana-appindicator3-dev"', task)
        self.assertNotIn('PACKAGES = ("libappindicator3-dev"', task)
        deploy = (ROOT / "deploy.py").read_text()
        # Before the tasks that reinstall the tray apps (nm-applet, 1-1).
        self.assertLess(deploy.index('"dev_libs"'), deploy.index('"vendor_apps"'))
        self.assertLess(deploy.index('"dev_libs"'), deploy.index('"desktop"'))

    def test_remmina_is_managed(self):
        native = applications.native_packages()
        for package in ("remmina", "remmina-plugin-rdp", "remmina-plugin-vnc", "remmina-plugin-secret"):
            self.assertIn(package, native)


if __name__ == "__main__":
    unittest.main()
