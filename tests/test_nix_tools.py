"""nix-user-tools: tool list rendering, regex-safe markers, PATH block order, migration (no nix)."""
import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from manage import applications as apps
from manage import nix_tools as nt
from manage import node, shell_tools as st

ROOT = Path(__file__).resolve().parents[1]


class ToolListTests(unittest.TestCase):
    def test_default_and_config_render(self):
        self.assertEqual(json.loads(nt.tools_json(nt.tools(None))), list(nt.DEFAULT_TOOLS))
        self.assertEqual(nt.tools(["jq", "btop", "jq"]), ("jq", "btop"))
        self.assertEqual(json.loads(nt.tools_json(nt.tools([]))), [])

    def test_rejects_non_attribute_names(self):
        for bad in ("python3Packages.foo", "a b", "x;rm", "", "${x}"):
            with self.assertRaises(ValueError, msg=bad):
                nt.tools([bad])
        with self.assertRaises(ValueError):
            nt.tools("jq")

    def test_excluded_tools(self):
        # rc in nixpkgs is the Plan 9 shell (ours is rustfs-cli); uv/node have other owners.
        self.assertFalse({"rc", "upmd", "uv", "nodejs", "dagger"} & set(nt.DEFAULT_TOOLS))

    def test_stamp_matches_shell_cat(self):
        with tempfile.TemporaryDirectory() as d:
            parts = (b"flake\n", b"lock\n", b'["jq"]\n')
            for name, data in zip(("flake.nix", "flake.lock", "tools.json"), parts):
                Path(d, name).write_bytes(data)
            out = subprocess.run(["bash", "-c", 'cat "$1"/flake.nix "$1"/flake.lock "$1"/tools.json | sha256sum',
                                  "_", d], capture_output=True, text=True, check=True).stdout.split()[0]
        self.assertEqual(nt.stamp(*parts), out)

    def test_flake_reads_tools_json(self):
        text = (ROOT / "nix/flake.nix").read_text()
        self.assertIn('github:NixOS/nixpkgs/nixos-26.05', text)
        self.assertIn('builtins.fromJSON (builtins.readFile ./tools.json)', text)
        self.assertIn('name = "t2-tools"', text)


class PathTests(unittest.TestCase):
    def test_markers_are_regex_safe(self):
        self.assertNotRegex(nt.PATH_MARKER, r"[()\[\]*+?|^$\\]")
        self.assertNotRegex(nt.BLESH_ATTACH_LINE, r"[()\[\]*+?|^$\\/]")

    def test_anchor_is_the_blesh_attach_begin_line_only(self):
        begin = st.BLESH_END_MARKER.format(mark="BEGIN")
        self.assertRegex(begin, nt.BLESH_ATTACH_LINE)
        for other in (st.BLESH_TOP_MARKER, st.BASH_MARKER, node.BASH_MARKER, nt.PATH_MARKER):
            for mark in ("BEGIN", "END"):
                self.assertNotRegex(other.format(mark=mark), nt.BLESH_ATTACH_LINE)
        self.assertNotRegex(st.BLESH_END_MARKER.format(mark="END"), nt.BLESH_ATTACH_LINE)

    def test_block_placement_before_attach_after_local_bin(self):
        """Simulate pyinfra's awk insert: before the first anchor match, else appended."""
        block = "\n".join((nt.PATH_MARKER.format(mark="BEGIN"), nt.PATH_BLOCK, nt.PATH_MARKER.format(mark="END")))
        node_block = "\n".join((node.BASH_MARKER.format(mark="BEGIN"), node.BASH_INIT, node.BASH_MARKER.format(mark="END")))
        attach = "\n".join((st.BLESH_END_MARKER.format(mark="BEGIN"), st.BLESH_END, st.BLESH_END_MARKER.format(mark="END")))
        for rc in (node_block + "\n" + attach + "\n", node_block + "\n"):
            with tempfile.NamedTemporaryFile("w", suffix=".bashrc", delete=False) as f:
                f.write(rc)
            try:
                out = subprocess.run(
                    ["awk", 'BEGIN {x=ARGV[2]; ARGV[2]=""} f!=1 && /' + nt.BLESH_ATTACH_LINE + '/ { print x; f=1} '
                     '{ print } END {if (f==0) print x }', f.name, block],
                    capture_output=True, text=True, check=True).stdout
            finally:
                os.unlink(f.name)
            pos = out.index(nt.PATH_MARKER.format(mark="BEGIN"))
            self.assertGreater(pos, out.index(node.BASH_MARKER.format(mark="END")))
            if "ble-attach" in rc:
                self.assertLess(pos, out.index(st.BLESH_END_MARKER.format(mark="BEGIN")))

    def test_bash_block_puts_nix_first_once(self):
        with tempfile.TemporaryDirectory() as home:
            Path(home, ".nix-profile/bin").mkdir(parents=True)
            nix = f"{home}/.nix-profile/bin"
            for start, want in (("/usr/bin:/bin", f"{nix}:/usr/bin:/bin"),
                                (f"/a:{nix}:/usr/bin", f"{nix}:/a:/usr/bin"),
                                (nix, nix)):
                out = subprocess.run(["/bin/bash", "-c", nt.PATH_BLOCK + "\n" + nt.PATH_BLOCK + '\necho "$PATH"'],
                                     env={"HOME": home, "PATH": start}, capture_output=True, text=True,
                                     check=True).stdout.strip()
                self.assertEqual(out, want)
            out = subprocess.run(["/bin/sh", "-c", nt.SESSION_PATH + 'echo "$PATH"'],
                                 env={"HOME": home, "PATH": "/usr/bin"}, capture_output=True, text=True).stdout.strip()
            self.assertEqual(out, f"{nix}:/usr/bin")

    def test_session_env_and_completions_include_nix(self):
        self.assertIn("nix_session_path", (ROOT / "tasks/desktop.py").read_text())
        self.assertIn("$HOME/.nix-profile/bin:", (ROOT / "files/shell/completions.sh").read_text())


class MigrationTests(unittest.TestCase):
    def test_migrated_tools_absent_from_release_route(self):
        migrated = set(nt.MIGRATED)
        self.assertFalse(migrated & set(apps.RELEASE_TOOLS))
        self.assertFalse(migrated & set(apps.release_tools()))
        self.assertEqual(set(apps.RELEASE_FALLBACK), migrated)
        cat = apps.catalog()
        for app_id in migrated:
            self.assertEqual(cat[app_id][0], "nix", app_id)

    def test_empty_nix_tools_falls_back_to_release(self):
        self.assertEqual(set(apps.release_tools(())), set(apps.RELEASE_TOOLS) | set(apps.RELEASE_FALLBACK))
        cat = apps.catalog(())
        self.assertEqual(cat["zellij"][0], "release")
        self.assertEqual(cat["podman-tui"][0], "excluded")   # Docker Engine replaced Podman

    def test_attributes_are_in_the_default_set(self):
        self.assertLessEqual(set(nt.MIGRATED.values()) | set(nt.NIX_PREFERRED.values()), set(nt.DEFAULT_TOOLS))


if __name__ == "__main__":
    unittest.main()


class ExtraToolsTests(unittest.TestCase):
    def test_extras_add_to_defaults_without_duplicates(self):
        from manage import nix_tools as nt
        merged = nt.tools(list(nt.tools(None)) + ["nchat", "btop"])
        self.assertEqual(merged[: len(nt.DEFAULT_TOOLS)], nt.DEFAULT_TOOLS)
        self.assertEqual(merged.count("btop"), 1)
        self.assertEqual(merged[-1], "nchat")
