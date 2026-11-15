"""Bootstrap contract checks; all installers and targets are disposable fixtures."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


BOOTSTRAP = Path(__file__).resolve().parents[1] / "bootstrap.sh"
REAL_UV = shutil.which("uv")
REAL_PYTHON = str(Path(sys.executable).resolve())


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "home"
        self.project = self.root / "project"
        self.bin = self.root / "bin"
        for path in (self.home, self.project, self.bin, self.root / "tmp"):
            path.mkdir()
        shutil.copyfile(BOOTSTRAP, self.project / "bootstrap.sh")
        self.write_project()
        (self.project / "uv.lock").write_text("fixture lock\n")
        for name in ("sh", "rm", "mktemp", "dirname"):
            (self.bin / name).symlink_to(shutil.which(name))
        (self.bin / "python3").symlink_to(REAL_PYTHON)
        self.env = {
            "PATH": str(self.bin), "HOME": str(self.home),
            "TMPDIR": str(self.root / "tmp"), "UV_OFFLINE": "1",
            "LOG": str(self.root / "calls.jsonl"),
            "UV_CACHE_DIR": str(self.root / "cache"),
        }
        self.install_fake_uv()
        self.executable("curl", """import os, pathlib, sys
pathlib.Path(os.environ['LOG']).open('a').write('curl ' + ' '.join(sys.argv[1:]) + '\\n')
if os.environ.get('CURL_FAIL'):
    sys.exit(22)
pathlib.Path(sys.argv[sys.argv.index('-o') + 1]).write_text(os.environ['INSTALLER'])
""")

    def executable(self, name, code):
        path = self.bin / name
        path.write_text(f"#!{REAL_PYTHON}\n" + code)
        path.chmod(0o755)
        return path

    def install_fake_uv(self):
        return self.executable("uv", """import json, os, sys
with open(os.environ['LOG'], 'a') as log:
    log.write(json.dumps({'args': sys.argv[1:], 'cwd': os.getcwd(),
        'environment': os.environ.get('UV_PROJECT_ENVIRONMENT')}) + '\\n')
if sys.argv[1:] == ['--version']:
    print('uv fixture existing')
else:
    sys.exit(int(os.environ.get('SYNC_FAIL', '0')))
""")

    def write_project(self, version="0.1.0"):
        (self.project / "pyproject.toml").write_text(
            '[project]\nname = "bootstrap-fixture"\n'
            f'version = "{version}"\nrequires-python = ">=3.11"\ndependencies = []\n'
            '[tool.uv]\npackage = false\n'
        )

    def run_bootstrap(self):
        return subprocess.run(
            ["/bin/sh", str(self.project / "bootstrap.sh")],
            env=self.env, cwd=self.home, capture_output=True, text=True,
        )

    def calls(self):
        log = Path(self.env["LOG"])
        return log.read_text() if log.exists() else ""

    def assert_failure(self, result, diagnostic):
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(diagnostic, result.stderr)

    def test_existing_uv_is_preserved_recorded_and_sync_is_locked_local(self):
        self.env["UV_PROJECT_ENVIRONMENT"] = str(self.root / "outside")
        self.env["UV_PROJECT"] = str(self.root / "outside")
        self.env["UV_WORKING_DIR"] = str(self.root / "outside")
        self.env["UV_FROZEN"] = "1"
        self.env["UV_CONFIG_FILE"] = str(self.root / "missing-config.toml")
        result = self.run_bootstrap()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("uv fixture existing", result.stdout)
        records = [json.loads(line) for line in self.calls().splitlines()]
        sync = records[-1]
        self.assertIn("--locked", sync["args"])
        self.assertEqual(sync["cwd"], str(self.project))
        self.assertEqual(sync["environment"], str(self.project / ".venv"))
        self.assertFalse((self.root / "outside").exists())

    def test_missing_python_is_reported_before_installer_or_sync(self):
        (self.bin / "python3").unlink()
        result = self.run_bootstrap()
        self.assert_failure(result, "Python 3.11")
        self.assertEqual(self.calls(), "")

    def test_unsupported_python_is_reported_before_installer_or_sync(self):
        (self.bin / "python3").unlink()
        self.executable("python3", "import sys\nsys.exit(1)\n")
        self.assert_failure(self.run_bootstrap(), "Python 3.11")
        self.assertEqual(self.calls(), "")

    def test_missing_curl_is_reported_even_with_existing_uv(self):
        (self.bin / "curl").unlink()
        self.assert_failure(self.run_bootstrap(), "curl")
        self.assertEqual(self.calls(), "")

    def test_failed_download_is_nonzero_and_cleans_temporary_installer(self):
        (self.bin / "uv").unlink()
        self.env["CURL_FAIL"] = "1"
        result = self.run_bootstrap()
        self.assert_failure(result, "download")
        self.assertIn("https://astral.sh/uv/0.13.8/install.sh", self.calls())
        self.assertIn("--proto =https --proto-redir =https", self.calls())
        self.assertEqual(list((self.root / "tmp").iterdir()), [])
        self.assertFalse((self.home / ".local").exists())

    def test_pinned_installer_is_user_local_and_failure_is_cleaned(self):
        (self.bin / "uv").unlink()
        self.env["UV_UNMANAGED_INSTALL"] = str(self.root / "outside")
        self.env["INSTALLER"] = 'test -z "${UV_UNMANAGED_INSTALL:-}" || exit 93\ntest "$UV_NO_MODIFY_PATH" = 1 || exit 91\ntest "$UV_INSTALL_DIR" = "$HOME/.local/bin" || exit 92\nexit 17\n'
        result = self.run_bootstrap()
        self.assert_failure(result, "install")
        self.assertEqual(list((self.root / "tmp").iterdir()), [])
        self.assertNotIn('"args"', self.calls())

    def test_pinned_install_success_syncs_with_installed_uv(self):
        fake_uv = self.bin / "uv"
        payload = self.root / "uv-payload"
        fake_uv.rename(payload)
        self.env["INSTALLER"] = (
            f'mkdir -p "$UV_INSTALL_DIR"\ncp "{payload}" "$UV_INSTALL_DIR/uv"\n'
        )
        for name in ("mkdir", "cp"):
            (self.bin / name).symlink_to(shutil.which(name))
        result = self.run_bootstrap()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.home / ".local/bin/uv").exists())
        self.assertIn('"--locked"', self.calls())
        self.assertEqual(list((self.root / "tmp").iterdir()), [])

    def test_sync_failure_is_nonzero(self):
        self.env["SYNC_FAIL"] = "42"
        self.assert_failure(self.run_bootstrap(), "sync")

    def test_symlink_environment_is_rejected_before_uv(self):
        outside = self.root / "outside"
        outside.mkdir()
        (self.project / ".venv").symlink_to(outside, target_is_directory=True)
        self.assert_failure(self.run_bootstrap(), ".venv")
        self.assertEqual(self.calls(), "")
        self.assertEqual(list(outside.iterdir()), [])

    def test_missing_lock_fails_before_installation(self):
        (self.project / "uv.lock").unlink()
        self.assert_failure(self.run_bootstrap(), "uv.lock")
        self.assertEqual(self.calls(), "")

    def test_existing_environment_with_system_packages_is_rejected(self):
        environment = self.project / ".venv"
        environment.mkdir()
        config = environment / "pyvenv.cfg"
        original = "include-system-site-packages = true\n"
        config.write_text(original)
        self.assert_failure(self.run_bootstrap(), "system site packages")
        self.assertEqual(self.calls(), "")
        self.assertEqual(config.read_text(), original)

    def test_local_workspace_is_rejected_before_uv(self):
        with (self.project / "pyproject.toml").open("a") as declaration:
            declaration.write('[tool.uv.workspace]\nmembers = ["child"]\n')
        self.assert_failure(self.run_bootstrap(), "workspace")
        self.assertEqual(self.calls(), "")

    def test_ancestor_workspace_is_rejected_before_uv(self):
        (self.root / "pyproject.toml").write_text('[tool.uv.workspace]\nmembers = ["project"]\n')
        self.assert_failure(self.run_bootstrap(), "workspace")
        self.assertEqual(self.calls(), "")

    @unittest.skipUnless(REAL_UV, "existing uv is needed for offline integration")
    def test_real_offline_sync_creates_local_environment_and_rejects_stale_lock(self):
        (self.bin / "uv").unlink()
        (self.bin / "uv").symlink_to(REAL_UV)
        (self.project / "uv.lock").unlink()
        lock = subprocess.run(
            [REAL_UV, "lock", "--offline", "--no-config", "--no-python-downloads", "--python", REAL_PYTHON],
            cwd=self.project, env=self.env, capture_output=True, text=True,
        )
        self.assertEqual(lock.returncode, 0, lock.stderr)
        before = (self.project / "uv.lock").read_bytes()
        self.env.update(UV_PROJECT_ENVIRONMENT=str(self.root / "outside"),
                        UV_FROZEN="1", UV_PROJECT=str(self.home), UV_WORKING_DIR=str(self.home),
                        UV_CONFIG_FILE=str(self.root / "missing-config.toml"))
        result = self.run_bootstrap()
        self.assertEqual(result.returncode, 0, result.stderr)
        python = self.project / ".venv/bin/python"
        check = subprocess.run([str(python), "-c", "import sys; print(sys.prefix); print(sys.base_prefix)"],
                               capture_output=True, text=True, check=True)
        prefix, base = check.stdout.splitlines()
        self.assertEqual(prefix, str(self.project / ".venv"))
        self.assertNotEqual(prefix, base)
        self.assertIn("include-system-site-packages = false", (self.project / ".venv/pyvenv.cfg").read_text())
        self.assertFalse((self.root / "outside").exists())
        self.write_project(version="0.2.0")
        result = self.run_bootstrap()
        self.assertNotEqual(result.returncode, 0, result.stderr)
        self.assertIn("lock", result.stderr)
        self.assertEqual((self.project / "uv.lock").read_bytes(), before)
