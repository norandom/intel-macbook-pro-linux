"""New guard: names, simulation parsing, archive inspection. No apt or sudo runs."""
from pathlib import Path
import unittest
from unittest.mock import patch

from manage import packages as guard

R = guard.PackageRequest


class RequestTests(unittest.TestCase):
    def test_valid_requests_pass(self):
        guard.validate_request(R(("btop", "neovim", "foo:amd64", "bar=1.2-3")))

    def test_invalid_prohibited_protected_and_duplicates_block(self):
        for packages in ((), ("Bad Name",), ("snapd",), ("flatpak",), ("gnome-software-plugin-snap",),
                         ("libflatpak0",), ("linux-image-generic",), ("grub-efi",), ("cryptsetup",),
                         ("initramfs-tools",), ("pipewire",), ("wireplumber",), ("apple-t2-audio-config",),
                         ("btop", "btop=1")):
            with self.subTest(packages=packages), self.assertRaises(RuntimeError):
                guard.validate_request(R(packages))


class SimulationTests(unittest.TestCase):
    def test_installs_and_dependency_upgrades_parse(self):
        out = ("Reading package lists...\nInst btop (1.4.6-2 Ubuntu:26.04/resolute [amd64])\n"
               "Inst libfoo1 [1.0] (1.1 Ubuntu:26.04/resolute [amd64])\nConf btop (1.4.6-2 Ubuntu [amd64])\n")
        self.assertEqual(guard._parse_simulation(out).installs, (("btop", "1.4.6-2"), ("libfoo1", "1.1")))

    def test_noop_has_no_installs(self):
        self.assertEqual(guard._parse_simulation("btop is already the newest version (1.4).\n").installs, ())

    def test_removals_and_transitive_protected_block(self):
        for out in ("Remv foo [1]\n", "Inst snapd (2 Ubuntu [amd64])\n", "Inst linux-image-7 (1 Ubuntu [amd64])\n",
                    "Inst initramfs-tools [1] (2 Ubuntu [all])\n"):
            with self.subTest(out=out), self.assertRaises(RuntimeError):
                guard._parse_simulation(out)


class ArchiveTests(unittest.TestCase):
    def test_protected_paths(self):
        for path in ("./boot/vmlinuz", "./etc/fstab", "./lib/modules/x/foo.ko", "./usr/share/initramfs-tools/hooks/x",
                     "./usr/lib/initramfs-tools/x", "./sbin/update-initramfs", "//etc/crypttab",
                     "./usr/lib/x86_64-linux-gnu/libcryptsetup.so.12", "./usr/lib/systemd/boot/efi/x.efi",
                     "./etc/modprobe.d/blacklist.conf", "./usr/lib/firmware/x.bin"):
            with self.subTest(path=path):
                self.assertTrue(guard.protected_path(path))
        for path in ("./usr/bin/btop", "./usr/share/doc/btop/README", "./etc/btop.conf"):
            with self.subTest(path=path):
                self.assertFalse(guard.protected_path(path))

    def test_check_archive_blocks_protected_payload_and_scripts(self):
        listing = "drwxr-xr-x root/root 0 2026-01-01 00:00 ./etc/initramfs-tools/hooks/x\n"
        with patch.object(guard, "_run", return_value=listing), self.assertRaisesRegex(RuntimeError, "protected path"):
            guard.check_archive(Path("/x.deb"))

        def fake_run(argv):
            if argv[1] == "--control":
                Path(argv[3], "postinst").write_bytes(b"#!/bin/sh\nupdate-initramfs -u\n")
                Path(argv[3], "control").write_bytes(b"Package: x\n")
            return "-rwxr-xr-x root/root 0 2026-01-01 00:00 ./usr/bin/x\n"
        with patch.object(guard, "_run", side_effect=fake_run), self.assertRaisesRegex(RuntimeError, "update-initramfs"):
            guard.check_archive(Path("/x.deb"))


if __name__ == "__main__":
    unittest.main()
