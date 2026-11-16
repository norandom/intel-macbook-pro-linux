import re
import unittest
from pathlib import Path

from manage import nix_tools as nt

ROOT = Path(__file__).resolve().parents[1]


class ConsistencyTests(unittest.TestCase):
    def test_font_rendering_has_one_default(self):
        defaults = {f: re.search(r'setting\("font_rendering", "(\w+)"\)', (ROOT / f).read_text()).group(1)
                    for f in ("tasks/fonts.py", "tasks/desktop.py")}
        self.assertEqual(len(set(defaults.values())), 1, defaults)

    def test_example_nix_list_matches_default_tools(self):
        text = (ROOT / "files/config.example.toml").read_text()
        block = text[text.index("# nix_tools = ["):]
        block = block[:block.index("]") + 1]
        self.assertEqual(re.findall(r'"([^"]+)"', block), list(nt.DEFAULT_TOOLS))

    def test_no_unread_config_keys_documented(self):
        self.assertNotIn("tailscale_exit_node", (ROOT / "files/config.example.toml").read_text())

    def test_tailscale_login_hint_only_when_needed(self):
        self.assertIn('_tailscale_state() != "Running"', (ROOT / "tasks/remote_access.py").read_text())
