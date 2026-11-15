"""~/.config/t2-mac-kde/config.toml loading and precedence (no pyinfra run)."""
import os
from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest.mock import patch

from manage import userconfig

ROOT = Path(__file__).resolve().parents[1]


class UserConfigTests(unittest.TestCase):
    def test_missing_file_is_empty_and_bad_file_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(userconfig.load(Path(tmp, "none.toml")), {})
            bad = Path(tmp, "bad.toml"); bad.write_text("panel_scale = = 1")
            with self.assertRaises(RuntimeError):
                userconfig.load(bad)

    def test_precedence_data_over_file_over_default(self):
        class Data(dict):
            pass
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "t2-mac-kde").mkdir()
            Path(tmp, "t2-mac-kde/config.toml").write_text("panel_scale = 1.6\ndesktop_left_reserve = 20\n")
            fake_host = type("H", (), {"data": Data(desktop_left_reserve=0)})()
            with patch.dict(os.environ, XDG_CONFIG_HOME=tmp), patch("pyinfra.host", fake_host), \
                 patch.object(userconfig, "_CACHE", None):
                self.assertEqual(userconfig.setting("panel_scale", "auto"), 1.6)
                self.assertEqual(userconfig.setting("desktop_left_reserve", 5), 0)   # --data wins
                self.assertEqual(userconfig.setting("bar_graphs", False), False)

    def test_example_parses_when_uncommented_keys_are_absent(self):
        self.assertEqual(tomllib.loads((ROOT / "files/config.example.toml").read_text()), {})


if __name__ == "__main__":
    unittest.main()
