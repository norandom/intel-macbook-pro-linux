"""[[mounts]] config checks, the generated settings file, and the shipped scripts/unit."""
import subprocess
import tempfile
import unittest
from pathlib import Path

from manage import mounts

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "files/mounts"
HOME = "/home/u"


def one(**kw):
    m = {"name": "filer", "type": "sshfs", "source": "filer:/share", "path": "~/Filer"}
    m.update(kw)
    return mounts.entries([m], HOME)


class ConfigTests(unittest.TestCase):
    def test_none_is_no_mounts(self):
        self.assertEqual(mounts.entries(None, HOME), [])

    def test_valid_entries_expand_the_path(self):
        [m] = one()
        self.assertEqual(m["path"], "/home/u/Filer")
        [r] = mounts.entries([{"name": "onedrive", "type": "rclone", "source": "OneDrive:", "path": "~/OneDrive",
                               "options": ["--onedrive-delta"], "offline": ["/Configs/"]}], HOME)
        self.assertEqual((r["options"], r["offline"]), (["--onedrive-delta"], ["Configs"]))

    def test_bad_entries_are_refused(self):
        for bad in ({"name": "Bad Name"}, {"type": "nfs"}, {"source": "noscheme"}, {"source": "-oProxy:x"},
                    {"path": "/mnt/x"}, {"path": "~/../etc"}, {"path": "~/a\nb"}, {"options": "x"},
                    {"options": ["-o", "x"]}, {"options": ["a,b"]}, {"offline": ["Docs"]}, {"extra": 1}):
            with self.subTest(bad=bad), self.assertRaises(RuntimeError):
                one(**bad)
        with self.assertRaises(RuntimeError):
            mounts.entries([{"name": "a", "type": "sshfs", "source": "h:/", "path": "~/X"},
                            {"name": "b", "type": "sshfs", "source": "h:/", "path": "~/X"}], HOME)
        with self.assertRaises(RuntimeError):
            mounts.entries({"name": "a"}, HOME)


class EnvFileTests(unittest.TestCase):
    def test_bash_reads_back_exact_values(self):
        [m] = mounts.entries([{"name": "x", "type": "rclone", "source": "Re mote:dir with 'quote'",
                               "path": "~/My Drive", "options": ["--a", "$(touch pwned)"],
                               "offline": ["A B", "C"]}], HOME)
        with tempfile.TemporaryDirectory() as tmp:
            env = Path(tmp) / "x.env"
            env.write_text(mounts.env_file(m))
            out = subprocess.run(["bash", "-c", f'. "{env}"; printf "%s|" "$TYPE" "$SOURCE" "$MOUNTPOINT" '
                                  '"${#OPTIONS[@]}" "${OPTIONS[1]}" "$OFFLINE_FOLDERS"'],
                                 capture_output=True, text=True, cwd=tmp, check=True).stdout
            self.assertEqual(out, "rclone|Re mote:dir with 'quote'|/home/u/My Drive|2|$(touch pwned)|A B\nC|")
            self.assertFalse((Path(tmp) / "pwned").exists())


class ShippedFilesTests(unittest.TestCase):
    def test_scripts_parse_and_hold_no_personal_data(self):
        subprocess.run(["bash", "-n", str(SRC / "t2-mount")], check=True)
        compile((SRC / "rclone-offline.py").read_text(), "rclone-offline.py", "exec")
        for f in SRC.iterdir():  # servers, users and folders belong in config.toml, not here
            text = f.read_text()
            self.assertNotRegex(text, r"/home/[a-z]|\b\d{1,3}(\.\d{1,3}){3}\b|\w+@[\w.-]+:", f.name)

    def test_unit_runs_in_both_sessions_and_unmounts_on_stop(self):
        unit = (SRC / "t2-mount@.service").read_text()
        self.assertIn("WantedBy=hypr-desktop.target plasma-workspace.target", unit)
        self.assertIn("ExecStop=%h/.local/libexec/t2-mac-kde/t2-mount --stop %i", unit)

    def test_config_options_override_rclone_defaults(self):
        # rclone keeps the last value of a repeated flag: the config's OPTIONS must come last.
        self.assertIn('"${flags[@]}" "${OPTIONS[@]}"', (SRC / "t2-mount").read_text())

    def test_task_is_in_the_full_deploy(self):
        self.assertIn('"mounts"', (ROOT / "deploy.py").read_text())
