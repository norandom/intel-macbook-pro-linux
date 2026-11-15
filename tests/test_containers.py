import unittest
from unittest import mock

from manage import containers as c


class SubidTests(unittest.TestCase):
    def test_parse_skips_junk(self):
        self.assertEqual(c.parse_subids("mc:100000:65536\n# x\nbad\nz:a:b\n"), [("mc", 100000, 65536)])

    def test_existing_range_retained(self):
        entries = c.parse_subids("mc:100000:65536\n")
        self.assertTrue(c.user_has_range(entries, "mc", 1000))
        self.assertFalse(c.user_has_range(entries, "other", 1001))

    def test_next_free_start_avoids_overlap(self):
        self.assertEqual(c.next_free_start([]), 100000)
        entries = c.parse_subids("a:100000:65536\nb:165536:65536\nc:400000:65536\n")
        self.assertEqual(c.next_free_start(entries), 231072)
        self.assertEqual(c.next_free_start(c.parse_subids("a:150000:10\n")), 150010)


class ConflictTests(unittest.TestCase):
    def test_docker_package_is_conflict(self):
        with mock.patch.object(c, "installed", side_effect=lambda p: p == "docker.io"), \
             mock.patch.object(c.shutil, "which", return_value="/usr/bin/docker"), \
             mock.patch.dict(c.os.environ, {}, clear=True):
            found = c.docker_conflicts()
        self.assertIn("package docker.io installed", found)
        self.assertIn("existing docker command at /usr/bin/docker", found)

    def test_own_shim_is_not_conflict(self):
        with mock.patch.object(c, "installed", side_effect=lambda p: p == c.DOCKER_SHIM), \
             mock.patch.object(c.shutil, "which", return_value="/usr/bin/docker"), \
             mock.patch.dict(c.os.environ, {}, clear=True):
            self.assertEqual(c.docker_conflicts(), [])

    def test_no_forbidden_packages(self):
        self.assertFalse({"snapd", "flatpak", "docker.io"} & set(c.PACKAGES + (c.DOCKER_SHIM,)))


if __name__ == "__main__":
    unittest.main()
