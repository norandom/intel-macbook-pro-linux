import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from manage import applications, nix_tools
from manage.rust_toolchains import REINSTALL_PATCHED

ROOT = Path(__file__).resolve().parents[1]
STUB = """#!/bin/sh
echo "$@" >> "$LOG"
case "$1 $2" in
  "default ") echo "1.100.0-x86_64-unknown-linux-gnu (default)" ;;
  "component list") printf 'cargo-x86_64-unknown-linux-gnu\\nclippy-x86_64-unknown-linux-gnu\\nrust-src\\nrust-std-aarch64-apple-darwin\\nrust-std-x86_64-pc-windows-gnu\\nrust-std-x86_64-unknown-linux-gnu\\nrustc-x86_64-unknown-linux-gnu\\nrust-analyzer-x86_64-unknown-linux-gnu\\n' ;;
  "toolchain install") case "$*" in *aarch64*) [ -n "$FAIL_TARGETS" ] && exit 1 ;; esac ;;
esac
"""


def nix_binary():
    for p in Path("/nix/store").glob("*-coreutils-*/bin/true"):
        if b"/nix/store/" in subprocess.run(["readelf", "-l", str(p)], capture_output=True).stdout:
            return p
    return None


class RustToolchainTests(unittest.TestCase):
    def test_rustup_from_ubuntu_not_nix(self):
        self.assertNotIn("rustup", nix_tools.DEFAULT_TOOLS)
        self.assertIn("rustup", applications.native_packages())

    @unittest.skipUnless(shutil.which("readelf") and nix_binary(), "readelf and a Nix-linked binary required")
    def test_only_patched_toolchains_are_reinstalled_with_their_components(self):
        with tempfile.TemporaryDirectory() as tmp:
            home, log, stub = Path(tmp) / "rustup", Path(tmp) / "log", Path(tmp) / "rustup-stub"
            stub.write_text(STUB)
            stub.chmod(0o755)
            for tc, src in (("1.100.0-x86_64-unknown-linux-gnu", nix_binary()), ("stable-x86_64-unknown-linux-gnu", Path("/usr/bin/true"))):
                (home / "toolchains" / tc / "bin").mkdir(parents=True)
                shutil.copy(src, home / "toolchains" / tc / "bin/rustc")
            env = dict(os.environ, RUSTUP_HOME=str(home), T2_RUSTUP=str(stub), LOG=str(log))
            subprocess.run(["bash", "-c", REINSTALL_PATCHED], env=env, check=True, capture_output=True)
            calls = log.read_text().splitlines()
            self.assertIn("toolchain uninstall 1.100.0-x86_64-unknown-linux-gnu", calls)
            self.assertIn("toolchain install 1.100.0-x86_64-unknown-linux-gnu --profile minimal -c clippy -c rust-src "
                          "-c rust-analyzer -t aarch64-apple-darwin -t x86_64-pc-windows-gnu", calls)
            self.assertFalse([c for c in calls if "stable" in c])
            self.assertEqual(calls[-1], "default 1.100.0-x86_64-unknown-linux-gnu")

    @unittest.skipUnless(shutil.which("readelf") and nix_binary(), "readelf and a Nix-linked binary required")
    def test_failed_install_falls_back_to_minimal(self):
        with tempfile.TemporaryDirectory() as tmp:
            home, log, stub = Path(tmp) / "rustup", Path(tmp) / "log", Path(tmp) / "rustup-stub"
            stub.write_text(STUB)
            stub.chmod(0o755)
            (home / "toolchains/1.100.0-x86_64-unknown-linux-gnu/bin").mkdir(parents=True)
            shutil.copy(nix_binary(), home / "toolchains/1.100.0-x86_64-unknown-linux-gnu/bin/rustc")
            env = dict(os.environ, RUSTUP_HOME=str(home), T2_RUSTUP=str(stub), LOG=str(log), FAIL_TARGETS="1")
            subprocess.run(["bash", "-c", REINSTALL_PATCHED], env=env, check=True, capture_output=True)
            self.assertIn("toolchain install 1.100.0-x86_64-unknown-linux-gnu --profile minimal", log.read_text().splitlines())

    def test_task_wiring(self):
        self.assertIn("REINSTALL_PATCHED", (ROOT / "tasks/nix_tools.py").read_text())


if __name__ == "__main__":
    unittest.main()
