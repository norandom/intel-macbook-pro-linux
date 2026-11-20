"""Wine bottles and the Scrivener task (offline: generated scripts and registry text)."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from manage import scrivener, wine
from manage.packages import PackageRequest, validate_request

ROOT = Path(__file__).resolve().parents[1]
BOTTLE = Path("/home/u/.local/share/wineprefixes/scrivener")


def sh_ok(script: str) -> None:
    subprocess.run(["bash", "-n"], input=script, text=True, check=True)


class BottleTests(unittest.TestCase):
    def test_one_bottle_per_app(self):
        home = Path("/home/u")
        self.assertEqual(wine.prefix("scrivener", home), BOTTLE)
        self.assertNotEqual(wine.prefix("other", home), BOTTLE)

    def test_packages_pass_the_guard(self):
        validate_request(PackageRequest(packages=wine.PACKAGES))

    def test_bottle_is_created_once_and_verbs_run_once(self):
        script = wine.bottle_script(BOTTLE, ("corefonts", "dotnet48"))
        sh_ok(script)
        self.assertIn('if [ ! -f "$WINEPREFIX/system.reg" ]', script)
        self.assertNotIn("rm -rf", script)  # a deploy never deletes a bottle
        for verb in ("corefonts", "dotnet48"):
            self.assertIn(f'grep -qx {verb} "$WINEPREFIX/winetricks.log"', script)
        # No Mono/Gecko dialog on first boot, but .NET is not overridden afterwards.
        self.assertIn("mscoree,mshtml=", script.split("wineboot")[0].splitlines()[-1])
        self.assertNotIn("mscoree", wine.env(BOTTLE))
        self.assertIn("winemenubuilder.exe=d", wine.env(BOTTLE))

    def test_registry(self):
        reg = wine.registry(154, "grayscale", False)
        self.assertTrue(reg.startswith("REGEDIT4\n"))
        self.assertIn('"LogPixels"=dword:0000009a', reg)
        self.assertIn('"FontSmoothingType"=dword:00000001', reg)
        self.assertIn('"Graphics"="x11"', reg)
        self.assertIn('"Segoe UI"="Noto Sans"', reg)
        self.assertIn('"FontSmoothingType"=dword:00000002', wine.registry(rendering="rgb"))
        self.assertIn('"Graphics"="wayland,x11"', wine.registry(wayland=True))
        for bad in ({"dpi": 20}, {"rendering": "subpixel"}):
            with self.assertRaises(ValueError):
                wine.registry(**bad)

    def test_installer_is_checked_before_it_runs(self):
        script = scrivener_install_script()
        sh_ok(script)
        check, run, record = (script.index("sha256sum -c"), script.index("wine /"),
                              script.index("> /home/u/.local/share/wineprefixes/scrivener/.t2"))
        self.assertLess(check, run)
        self.assertLess(run, record)
        self.assertIn("test -f '/home/u/.local/share/wineprefixes/scrivener/drive_c/Program Files/Scrivener3/Scrivener.exe'", script)
        self.assertIn("--proto '=https'", script)


def scrivener_install_script() -> str:
    return wine.installer_script(BOTTLE, scrivener.URL, scrivener.SHA256, scrivener.VERSION,
                                 BOTTLE / ".t2-mac-kde-version", scrivener.INSTALLER_ARGS,
                                 scrivener.install_dir(BOTTLE) / "Scrivener.exe")


class ScrivenerTests(unittest.TestCase):
    def test_pin(self):
        self.assertRegex(scrivener.VERSION, r"^\d+\.\d+\.\d+\.\d+$")
        self.assertRegex(scrivener.SHA256, r"^[0-9a-f]{64}$")
        self.assertTrue(scrivener.URL.startswith("https://"))
        self.assertIn("unattended", scrivener.INSTALLER_ARGS)

    def test_launcher_fixups_run_and_are_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "Program Files/Scrivener3"
            (directory / "texttospeech").mkdir(parents=True)
            conf = directory / "qt.conf"
            conf.write_text("[Platforms]\nWindowsArguments = darkmode=1\n")
            for _ in range(2):
                subprocess.run(["sh", "-eu"], input=scrivener.fixups(directory), text=True, check=True)
            self.assertFalse((directory / "texttospeech").exists())
            self.assertEqual(conf.read_text(), "[Platforms]\nWindowsArguments = darkmode=1,fontengine=freetype\n")
            conf.write_text("[Paths]\nPrefix=.\n")
            subprocess.run(["sh", "-eu"], input=scrivener.fixups(directory), text=True, check=True)
            self.assertIn("[Platforms]\nWindowsArguments = fontengine=freetype\n", conf.read_text())

    def test_launcher(self):
        text = scrivener.launcher(BOTTLE)
        sh_ok(text)
        self.assertTrue(text.startswith("#!/bin/sh\n"))
        self.assertLess(text.index("texttospeech"), text.index("exec wine"))
        self.assertIn("Scrivener3/Scrivener.exe'", text)
        self.assertIn("cryptbase=b", text)

    def test_task_is_opt_in_and_in_deploy(self):
        task = (ROOT / "tasks/scrivener.py").read_text()
        self.assertIn('setting("scrivener", False)', task)
        self.assertRegex((ROOT / "deploy.py").read_text(), r'"scrivener",')
        self.assertIn("# scrivener = false", (ROOT / "files/config.example.toml").read_text())
        # The license key never goes into the repo or the config.
        self.assertIsNone(re.search(r"licen[cs]e_?key|serial", task, re.I))

    def test_desktop_entry(self):
        entry = wine.desktop_entry("Scrivener", "c", Path("/home/u/.local/bin/scrivener"),
                                   Path("/i.png"), "Office;WordProcessor;", "scrivener.exe")
        self.assertIn("Categories=Office;WordProcessor;\n", entry)
        self.assertIn("StartupWMClass=scrivener.exe\n", entry)


if __name__ == "__main__":
    unittest.main()
