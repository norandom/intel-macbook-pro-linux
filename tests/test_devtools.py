"""Compiler default stays user-only: GCC for root, apt, DKMS, Kbuild and Debian package builds."""
from pathlib import Path
import re
import unittest

from manage import shell_tools as st

ROOT = Path(__file__).resolve().parents[1]


class DevtoolsTests(unittest.TestCase):
    def test_icx_only_when_configured_and_installed(self):
        self.assertNotIn("CC=icx", st.devtools_block("", False))
        block = st.devtools_block("icx", False)
        self.assertIn(f"[ -x {st.ICX_BIN}/icx ]", block)
        self.assertIn('PATH="$PATH:', block)            # appended: never shadows gcc/clang
        self.assertIn("if [[ $- == *i* ]]", block)       # interactive shells only

    def test_debian_builds_and_dkms_forced_to_gcc(self):
        block = st.devtools_block("icx", False)
        self.assertIn("dpkg-buildpackage() { CC=gcc CXX=g++", block)
        self.assertIn("debuild() { CC=gcc CXX=g++", block)
        self.assertIn("unset CC CXX", st.DKMS_GCC_ONLY)

    def test_cc_never_written_system_or_session_wide(self):
        for path in [ROOT / "tasks/desktop.py", ROOT / "tasks/resource_policy.py", *ROOT.glob("files/**/*.service")]:
            text = path.read_text()
            self.assertIsNone(re.search(r"export CC=|Environment=.*\bCC=", text), path)

    def test_safe_chain_pinned_and_aliases_guarded(self):
        name, version = st.SAFE_CHAIN
        self.assertRegex(version, r"^\d+\.\d+\.\d+$")
        block = st.devtools_block("", True)
        self.assertIn("command -v aikido-npm >/dev/null && alias npm=aikido-npm", block)


if __name__ == "__main__":
    unittest.main()
