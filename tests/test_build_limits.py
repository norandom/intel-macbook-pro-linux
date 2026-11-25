"""Heavy jobs leave the desktop a free core: terminal affinity, job variables, containers.slice."""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from manage import build_limits as bl
from manage import containers as c

ROOT = Path(__file__).resolve().parents[1]


def fake_sys(root: Path, cores: int = 8):
    """8 cores, 16 threads, siblings n and n+8 (this MacBook's layout)."""
    (root / "online").write_text(f"0-{2 * cores - 1}\n")
    for n in range(2 * cores):
        t = root / f"cpu{n}/topology"
        t.mkdir(parents=True)
        core = n % cores
        t.joinpath("thread_siblings_list").write_text(f"{core},{core + cores}\n")


class BuildLimitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        fake_sys(Path(self.tmp.name))
        self.online, self.groups = bl.topology(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_first_core_with_both_threads_stays_free(self):
        cpus = bl.allowed(self.online, self.groups, 1)
        self.assertEqual(bl.fmt_list(cpus), "1-7,9-15")
        self.assertEqual(bl.jobs(cpus, 0), 14)
        self.assertEqual(bl.jobs(cpus, 6), 6)
        self.assertEqual(bl.allowed(self.online, self.groups, 0), self.online)          # off
        self.assertEqual(bl.fmt_list(bl.allowed(self.online, self.groups, 99)), "7,15")  # one core always left

    def test_list_round_trip(self):
        self.assertEqual(bl.parse_list("0-3,8,10-11"), [0, 1, 2, 3, 8, 10, 11])
        self.assertEqual(bl.fmt_list([0, 1, 2, 3, 8, 10, 11]), "0-3,8,10-11")

    def test_bash_shell_limits_itself_and_allcores_lifts_it(self):
        cpus = bl.allowed(self.online, self.groups, 1)
        block = bl.bash_block(cpus, self.online, 14)
        self.assertIn("taskset -cp 1-7,9-15 $$", block)
        for var in ("GOMAXPROCS", "CARGO_BUILD_JOBS", "NEXTEST_TEST_THREADS", "RUST_TEST_THREADS",
                    "PYTEST_XDIST_AUTO_NUM_WORKERS", "CMAKE_BUILD_PARALLEL_LEVEL"):
            self.assertIn(f'export {var}="${{{var}:-14}}"', block)       # a value you set wins
        self.assertIn("allcores() { taskset -c 0-15 env -u GOMAXPROCS", block)
        self.assertNotIn("taskset -cp", bl.bash_block(self.online, self.online, 16))  # reserved_cores = 0
        subprocess.run(["bash", "-n"], input=block, text=True, check=True)

    def test_fish_conf_is_interactive_only(self):
        conf = bl.fish_conf(bl.allowed(self.online, self.groups, 1), self.online, 14)
        self.assertIn("status is-interactive; or exit", conf)
        self.assertIn("taskset -cp 1-7,9-15 $fish_pid", conf)
        self.assertIn("set -q GOMAXPROCS; or set -gx GOMAXPROCS 14", conf)

    def test_containers_in_top_level_slice_off_the_desktop_core(self):
        self.assertNotIn("-", bl.SLICE)                                  # a dash would nest the slice
        unit = bl.slice_unit(bl.allowed(self.online, self.groups, 1))
        self.assertIn("AllowedCPUs=1-7,9-15", unit)
        self.assertIn(f"CPUWeight={bl.SLICE_WEIGHT}", unit)
        self.assertEqual(c.daemon_config(bl.SLICE)["cgroup-parent"], "containers.slice")
        self.assertNotIn("cgroup-parent", c.daemon_config(""))
        self.assertTrue(c.daemon_config(bl.SLICE)["ip-forward-no-drop"])
        json.dumps(c.daemon_config(bl.SLICE))

    def test_tasks_wire_it_up(self):
        shell = (ROOT / "tasks/shell.py").read_text()
        self.assertIn("marker=bl.MARKER, content=bl.bash_block(heavy_cpus, online, heavy_jobs)", shell)
        self.assertIn('conf.d/t2-build-limits.fish', shell)
        containers = (ROOT / "tasks/containers.py").read_text()
        self.assertIn("c.daemon_config(bl.SLICE if reserved > 0 else \"\")", containers)
        self.assertIn('dest=f"/etc/systemd/system/{bl.SLICE}"', containers)
        self.assertIn("_if=slice_unit.did_change", containers)


if __name__ == "__main__":
    unittest.main()
