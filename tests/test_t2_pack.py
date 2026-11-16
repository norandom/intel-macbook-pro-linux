import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from manage import t2_pack

ROOT = Path(__file__).resolve().parents[1]


class Manifest(unittest.TestCase):
    def test_manifest_loads_and_has_sums(self):
        pack = t2_pack.load()
        self.assertTrue(pack["id"].startswith("t2-"))
        self.assertIn("linux-t2", pack["packages"])
        sums = t2_pack.read_sums(t2_pack.sums_file(pack))
        for name, ver in pack["packages"].items():
            self.assertTrue(any(k.startswith(f"{name}_{ver}_") for k in sums), name)

    def test_kernel_image_matches_metapackage(self):
        p = t2_pack.load()["packages"]
        kver = p["linux-t2"].removesuffix("-resolute")
        self.assertEqual(p[f"linux-image-{kver}-t2-resolute"], kver)
        self.assertEqual(p[f"linux-headers-{kver}-t2-resolute"], kver)
        self.assertEqual(t2_pack.load()["id"], f"t2-{kver}")

    def test_rejects_bad_entries(self):
        with tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False) as f:
            f.write('id = "t2-1"\n[packages]\n"linux-t2" = "1.0; rm -rf /"\n')
        with self.assertRaises(ValueError):
            t2_pack.load(Path(f.name))

    def test_pref_never_forces_downgrade(self):
        text = t2_pack.pref(t2_pack.load())
        self.assertIn("Package: linux-t2\nPin: version 7.3.4-3-resolute\nPin-Priority: 990", text)
        self.assertLess(t2_pack.PRIORITY, 1000)
        self.assertGreater(t2_pack.PRIORITY, 500)


class Backup(unittest.TestCase):
    def test_backup_detects_changed_deb(self):
        pack = {"id": "t2-test", "packages": {"foo": "1.0"}}
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "foo_1.0_amd64.deb").write_bytes(b"good")
            with mock.patch.object(t2_pack, "SUMS_DIR", d / "packs"):
                t2_pack.backup(pack, d, write_sums=True)          # records
                t2_pack.backup(pack, d)                           # verifies
                (d / "foo_1.0_amd64.deb").write_bytes(b"evil")
                with self.assertRaises(RuntimeError):
                    t2_pack.backup(pack, d)


class Wiring(unittest.TestCase):
    def test_deploy_and_boundary(self):
        self.assertIn('"t2_pack"', (ROOT / "deploy.py").read_text())
        self.assertIn("T2 pack pin", (ROOT / ".kiro/steering/protected-system-boundary.md").read_text())
        task = (ROOT / "tasks/t2_pack.py").read_text()
        self.assertNotIn("apt-get install", task)
        self.assertNotIn("apt install", task)

    def test_tool_help(self):
        r = subprocess.run([str(ROOT / ".venv/bin/python"), str(ROOT / "tools/t2-pack"), "--help"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        self.assertIn("release", r.stdout)


class BackgroundUpdates(unittest.TestCase):
    def test_conf_turns_every_periodic_job_off(self):
        text = t2_pack.no_background_conf()
        for key in ("Update-Package-Lists", "Download-Upgradeable-Packages", "Unattended-Upgrade", "AutocleanInterval"):
            self.assertIn(f'APT::Periodic::{key} "0";', text)
        self.assertTrue(t2_pack.NO_BG_CONF.startswith("/etc/apt/apt.conf.d/99-"))  # after 20auto-upgrades
        self.assertIn("unattended-upgrades.service", t2_pack.NO_BG_TIMERS)

    def test_apt_waits_for_lock(self):
        from manage import packages
        from manage.packages import PackageRequest
        self.assertIn("DPkg::Lock::Timeout=300", packages._apt_args(PackageRequest(("foo",))))
