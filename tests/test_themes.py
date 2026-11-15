"""Fixture checks for the coordinated-themes commands (disposable HOME, stubbed live tools)."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEMES = ROOT / "files/themes"
SWITCH = THEMES / "bin/hypr-termtheme"
TERM = THEMES / "bin/hypr-term"
PALETTES = ("cobalt", "navy", "fixedsys", "cream", "petrol")


class ThemeCommandTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.bin = self.home / "stubbin"
        self.bin.mkdir()
        # Stubs: no real process is ever signalled; terminator echoes its argv.
        for name, body in (("pkill", "exit 1"), ("terminator", 'printf "%s\\n" "$@"; exit 7')):
            p = self.bin / name
            p.write_text(f"#!/bin/sh\n{body}\n")
            p.chmod(0o755)
        self.env = {"HOME": str(self.home), "PATH": f"{self.bin}:/usr/bin:/bin", "LANG": "C.UTF-8"}
        cfg = self.home / ".config"
        for t in PALETTES:  # installed assets, as tasks/themes.py puts them
            for src, dest in ((f"ghostty/themes/{t}", f"ghostty/themes/{t}"),
                              (f"foot/themes/{t}.ini", f"foot/themes/{t}.ini"),
                              (f"btop/{t}.theme", f"btop/themes/{t}.theme")):
                d = cfg / dest
                d.parent.mkdir(parents=True, exist_ok=True)
                d.write_bytes((THEMES / src).read_bytes())
        (self.home / ".claude/themes").mkdir(parents=True)
        for t in PALETTES:
            (self.home / f".claude/themes/{t}.json").write_bytes((THEMES / f"claude/{t}.json").read_bytes())

    def tearDown(self):
        self.tmp.cleanup()

    def run_cmd(self, cmd, *args):
        return subprocess.run([str(cmd), *args], env=self.env, capture_output=True, text=True)

    @property
    def state(self):
        p = self.home / ".local/state/terminator-profile"
        return p.read_text() if p.exists() else None

    def test_cycle_order_wraps_both_ways(self):
        seen = [self.run_cmd(SWITCH, "next").returncode == 0 and self.state for _ in range(5)]
        self.assertEqual(seen, ["navy\n", "fixedsys\n", "cream\n", "petrol\n", "default\n"])
        self.assertEqual(self.run_cmd(SWITCH).returncode, 0)  # empty = next
        self.assertEqual(self.state, "navy\n")
        self.run_cmd(SWITCH, "prev")
        self.run_cmd(SWITCH, "prev")
        self.assertEqual(self.state, "petrol\n")

    def test_apply_keeps_selection_and_sets_apps(self):
        self.run_cmd(SWITCH, "cream")
        (self.home / ".config/foot/theme.ini").unlink()
        r = self.run_cmd(SWITCH, "apply")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.state, "cream\n")
        cfg = self.home / ".config"
        self.assertEqual((cfg / "foot/theme.ini").read_bytes(), (THEMES / "foot/themes/cream.ini").read_bytes())
        self.assertEqual((cfg / "ghostty/theme").read_bytes(), (THEMES / "ghostty/themes/cream").read_bytes())
        self.assertIn('color_theme = "cream"', (cfg / "btop/btop.conf").read_text())
        self.assertEqual(json.loads((self.home / ".claude/settings.json").read_text())["theme"], "custom:cream")
        self.assertIn("unchanged", self.run_cmd(SWITCH, "apply").stdout)

    def test_invalid_arguments_change_nothing(self):
        self.run_cmd(SWITCH, "navy")
        for args in (("bogus",), ("navy", "extra"), ("cobalt",)):
            self.assertEqual(self.run_cmd(SWITCH, *args).returncode, 2)
        self.assertEqual(self.state, "navy\n")

    def test_invalid_state_is_an_error_but_profile_repairs_it(self):
        st = self.home / ".local/state/terminator-profile"
        st.parent.mkdir(parents=True, exist_ok=True)
        st.write_text("navy\npetrol\n")
        self.assertEqual(self.run_cmd(SWITCH, "next").returncode, 1)
        self.assertEqual(self.run_cmd(TERM).returncode, 1)
        self.assertEqual(self.run_cmd(SWITCH, "petrol").returncode, 0)
        self.assertEqual(self.state, "petrol\n")

    def test_jsonc_settings_left_untouched(self):
        code = self.home / ".config/Code/User/settings.json"
        code.parent.mkdir(parents=True)
        text = '{\n  // mine\n  "editor.fontSize": 10,\n}\n'
        code.write_text(text)
        plain = self.home / ".config/Positron/User/settings.json"
        plain.parent.mkdir(parents=True)
        plain.write_text('{\n  "files.autoSave": "on"\n}\n')
        r = self.run_cmd(SWITCH, "fixedsys")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(code.read_text(), text)
        self.assertIn("code: unapplied", r.stdout)
        prefs = json.loads(plain.read_text())
        self.assertEqual(prefs["files.autoSave"], "on")
        self.assertEqual(prefs["workbench.colorTheme"], "debian-hypr Fixedsys")
        self.assertEqual(prefs["editor.fontSize"], 12)

    def test_btop_conf_keeps_other_lines(self):
        conf = self.home / ".config/btop/btop.conf"
        conf.write_text('# mine\ncolor_theme = "Default"\nupdate_ms = 500\n')
        self.run_cmd(SWITCH, "navy")
        self.assertEqual(conf.read_text(), '# mine\ncolor_theme = "navy"\nupdate_ms = 500\n')

    def test_hypr_term_passes_arguments_and_exit(self):
        self.run_cmd(SWITCH, "petrol")
        r = self.run_cmd(TERM, "-x", "sh -c 'a b'", "")
        self.assertEqual(r.returncode, 7)
        self.assertEqual(r.stdout, "-p\npetrol\n-x\nsh -c 'a b'\n\n")

    def test_hypr_term_missing_terminator(self):
        (self.bin / "terminator").unlink()
        self.env["PATH"] = str(self.bin) + ":/nonexistent"
        r = subprocess.run(["/bin/sh", str(TERM)], env=self.env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 127)


class ThemeAssetTests(unittest.TestCase):
    def test_all_five_palettes_present(self):
        for t in PALETTES:
            for rel in (f"btop/{t}.theme", f"claude/{t}.json", f"ghostty/themes/{t}", f"ghostty/themes/{t}.css",
                        f"foot/themes/{t}.ini", f"sublime/debian-hypr-{t}.sublime-color-scheme",
                        f"vscode/debian-hypr-themes/themes/{t}-color-theme.json"):
                self.assertTrue((THEMES / rel).is_file(), rel)
        cfg = (THEMES / "terminator/config").read_text()
        for p in ("default", "navy", "fixedsys", "cream", "petrol"):
            self.assertIn(f"  [[{p}]]", cfg)

    def test_foot_themes_use_ubuntu_125_dialect(self):
        for t in PALETTES:
            text = (THEMES / f"foot/themes/{t}.ini").read_text()
            self.assertIn("\n[colors]\n", text)
            self.assertNotIn("\n[colors-dark]", text)


if __name__ == "__main__":
    unittest.main()
