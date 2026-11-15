"""Fixture-only checks for tasks/fonts.py helpers: no network, no host font changes."""

import hashlib
import io
import os
import subprocess
import tarfile
import tempfile
import unittest
import xml.dom.minidom
from pathlib import Path
from unittest.mock import patch

import jinja2

from manage import fonts as F

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "files/fonts/hypr-xfonts"


def stub(bindir: Path, name: str, body: str) -> None:
    p = bindir / name
    p.write_text("#!/bin/sh\n" + body + "\n")
    p.chmod(0o755)


class ManifestTests(unittest.TestCase):
    def test_pins_valid_and_names(self):
        F.validate_manifest()
        self.assertEqual(F.nerd_files("JetBrainsMono")[0], "JetBrainsMonoNerdFont-Regular.ttf")
        self.assertEqual(len(F.nerd_files("FiraCode")), 6)

    def test_bad_pin_rejected(self):
        with patch.dict(F.EXTRA_FONTS, {"x.ttf": ("http://example/x.ttf", "0" * 64)}):
            with self.assertRaises(ValueError):
                F.validate_manifest()

    def test_template_renders_valid_xml(self):
        src = (ROOT / "templates/fontconfig/60-t2-fonts.conf.j2").read_text()
        for mode in F.RENDERING_MODES:
            out = jinja2.Template(src).render(font_rendering=mode)
            xml.dom.minidom.parseString(out)
            self.assertIn("JetBrainsMono Nerd Font", out)
            self.assertIn("Symbola", out)
            self.assertEqual("lcddefault" in out, mode == "rgb")

    def test_user_conf_conflicts(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "fonts.conf"
            self.assertEqual(F.user_conf_conflicts(p), [])
            p.write_text('<edit name="rgba"><const>rgb</const></edit>')
            self.assertEqual(F.user_conf_conflicts(p), ["rgba"])


class NerdInstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        self.bin = self.d / "bin"
        self.bin.mkdir()
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:xz") as tar:
            for name in ("TestNerdFont-Regular.ttf", "TestNerdFont-Bold.ttf", "README.md"):
                data = name.encode()
                info = tarfile.TarInfo(name)
                info.size = len(data)
                tar.addfile(info, io.BytesIO(data))
        self.archive = self.d / "Test.tar.xz"
        self.archive.write_bytes(buf.getvalue())
        self.sha = hashlib.sha256(buf.getvalue()).hexdigest()
        # curl stub: copy the fixture to the -o target
        stub(self.bin, "curl", f'while [ $# -gt 0 ]; do [ "$1" = -o ] && o=$2; shift; done; cp "{self.archive}" "$o"')
        stub(self.bin, "fc-cache", "exit 0")
        self.env = dict(os.environ, PATH=f"{self.bin}:{os.environ['PATH']}")
        self.dest = self.d / "fonts/test-nerd"

    def tearDown(self):
        self.tmp.cleanup()

    def run_script(self, sha):
        with patch.dict(F.NERD_FONTS, {"Test": (sha, ("Regular", "Bold"))}):
            script = F.nerd_script("Test", self.dest)
            r = subprocess.run(["sh", "-c", script], env=self.env, capture_output=True)
            return r, F.nerd_installed(self.dest, "Test")

    def test_install_verify_and_damage(self):
        r, ok = self.run_script(self.sha)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(ok)
        self.assertFalse((self.dest / "README.md").exists())
        (self.dest / "TestNerdFont-Bold.ttf").write_bytes(b"damaged")
        with patch.dict(F.NERD_FONTS, {"Test": (self.sha, ("Regular", "Bold"))}):
            self.assertFalse(F.nerd_installed(self.dest, "Test"))

    def test_bad_checksum_keeps_previous_family(self):
        self.run_script(self.sha)
        before = (self.dest / ".sha256sums").read_text()
        r, ok = self.run_script("0" * 64)
        self.assertNotEqual(r.returncode, 0)
        self.assertTrue(ok)
        self.assertEqual((self.dest / ".sha256sums").read_text(), before)
        self.assertFalse(Path(f"{self.dest}.new").exists())


class HelperTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        self.bin = self.d / "bin"
        self.bin.mkdir()
        self.core = self.d / "core"
        self.core.mkdir()
        (self.core / "fonts.dir").write_text("2\n")
        self.log = self.d / "log"
        stub(self.bin, "sleep", "exit 0")
        self.env = dict(os.environ, PATH=f"{self.bin}:{os.environ['PATH']}",
                        HYPR_XFONTS_DIR=str(self.core), XDG_RUNTIME_DIR=str(self.d), DISPLAY=":9")

    def tearDown(self):
        self.tmp.cleanup()

    def xset(self, fontpath, q_rc=0, rehash_rc=0):
        stub(self.bin, "xset", f'''echo "$*" >> "{self.log}"
case "$1" in
  q) [ {q_rc} -eq 0 ] || exit 1; printf 'Font Path:\\n  {fontpath}\\n';;
  fp) exit {rehash_rc};;
esac''')

    def run_helper(self, *args):
        return subprocess.run([str(HELPER), *args], env=self.env, capture_output=True, text=True)

    def calls(self):
        return self.log.read_text().splitlines() if self.log.exists() else []

    def test_usage(self):
        self.assertEqual(self.run_helper("x").returncode, 2)

    def test_skipped_without_index(self):
        (self.core / "fonts.dir").unlink()
        self.xset("built-ins")
        r = self.run_helper()
        self.assertEqual(r.returncode, 0)
        self.assertIn("skipped", r.stderr)
        self.assertEqual(self.calls(), [])

    def test_adds_once_and_rehashes(self):
        self.xset("/usr/share/fonts/X11/misc," + str(self.core) + "x,built-ins")
        self.assertEqual(self.run_helper().returncode, 0)
        self.assertIn(f"+fp {self.core}", self.calls())
        self.assertEqual(self.calls()[-1], "fp rehash")

    def test_present_not_added_again(self):
        self.xset(f"built-ins,{self.core}")
        self.assertEqual(self.run_helper().returncode, 0)
        self.assertFalse(any(c.startswith("+fp") for c in self.calls()))

    def test_display_unavailable_bounded(self):
        self.xset("", q_rc=1)
        r = self.run_helper()
        self.assertEqual(r.returncode, 1)
        self.assertEqual(len(self.calls()), 41)

    def test_rehash_failure(self):
        self.xset("built-ins", rehash_rc=1)
        self.assertEqual(self.run_helper().returncode, 1)


if __name__ == "__main__":
    unittest.main()
