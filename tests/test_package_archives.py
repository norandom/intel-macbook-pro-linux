"""Locating downloaded archives for the package guard (multiarch)."""
import unittest
from pathlib import Path
from unittest import mock

from manage import packages as guard


class MultiarchArchiveTests(unittest.TestCase):
    def test_native_package_does_not_match_its_i386_twin(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            for arch in ("amd64", "i386"):
                (cache / f"libfoo_1.0-1_{arch}.deb").touch()
            (cache / "libbar_2%3a1.0_all.deb").touch()
            with mock.patch.object(guard, "_native_arch", return_value="amd64"), \
                    mock.patch.object(guard, "Path", side_effect=lambda p: cache if p == "/var/cache/apt/archives" else Path(p)):
                self.assertEqual(guard._deb_path("libfoo", "1.0-1").name, "libfoo_1.0-1_amd64.deb")
                self.assertEqual(guard._deb_path("libfoo:i386", "1.0-1").name, "libfoo_1.0-1_i386.deb")
                self.assertEqual(guard._deb_path("libbar", "2:1.0").name, "libbar_2%3a1.0_all.deb")


if __name__ == "__main__":
    unittest.main()
