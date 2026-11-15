"""Package planning fixtures never execute apt or mutate host configuration."""

import dataclasses
import subprocess
import unittest
from unittest.mock import patch

from manage import packages as guard


class PackagePlanningTests(unittest.TestCase):
    def test_contract_and_ubuntu_request(self):
        request = guard.PackageRequest(("btop:amd64=1.4.6-2",), "ubuntu")
        with patch.object(guard, "_REVIEWS", (self.review(),)):
            self.assertIsNone(guard.validate_request(request))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            request.source = "other"

    def review(self, **changes):
        fields = dict(package="btop", version="1.4.6-2", architecture="amd64",
                      deb_sha256="a" * 64, baseline_sha256="b" * 64,
                      evidence="fixture-review: native Ubuntu archive, control/files and all hook effects reviewed",
                      native=True, scripts_reviewed=True, triggers_reviewed=True,
                      apt_hooks_reviewed=True, paths=("/usr/bin/btop",))
        fields.update(changes)
        return guard._PackageReview(**fields)

    def plan(self, simulation=None, *, reviews=None, metadata=None, baseline="b" * 64, request=None):
        if simulation is None:
            simulation = ("Reading package lists...\nBuilding dependency tree...\n"
                          "Reading state information...\nSolving dependencies...\n"
                          "The following NEW packages will be installed:\n  btop\n"
                          "0 upgraded, 1 newly installed, 0 to remove and 2 not upgraded.\n"
                          "Inst btop (1.4.6-2 Ubuntu:26.04/resolute [amd64])\n"
                          "Conf btop (1.4.6-2 Ubuntu:26.04/resolute [amd64])\n")
        if metadata is None:
            metadata = ("Package: btop\nVersion: 1.4.6-2\nArchitecture: amd64\n"
                        "Origin: Ubuntu\nSHA256: " + "a" * 64 + "\n")
        request = request or guard.PackageRequest(("btop",), "ubuntu")
        def run(argv, **kwargs):
            self.assertIsInstance(argv, tuple)
            self.assertEqual(kwargs["env"]["LC_ALL"], "C")
            self.assertEqual(kwargs["env"]["LANG"], "C")
            self.assertFalse(kwargs.get("shell", False))
            self.assertEqual(kwargs["timeout"], 30)
            if argv[0] == "/usr/bin/apt-get":
                self.assertEqual(argv, ("/usr/bin/apt-get", "--simulate", "--no-install-recommends",
                                        "--no-remove", "install", *request.packages))
                return subprocess.CompletedProcess(argv, 0, simulation, "")
            self.assertEqual(argv[:2], ("/usr/bin/apt-cache", "show"))
            self.assertIn(argv[2], ("btop=1.4.6-2", "btop:amd64=1.4.6-2"))
            return subprocess.CompletedProcess(argv, 0, metadata, "")
        with patch.object(guard, "_REVIEWS", tuple(reviews or (self.review(),))), \
             patch.object(guard, "_baseline_digest", return_value=baseline), \
             patch.object(guard.subprocess, "run", side_effect=run) as runner:
            result = guard.inspect_plan(request)
            self.assertEqual(runner.call_count, 2)
            return result

    def test_native_reviewed_plan_retains_resolved_version_and_has_no_removals(self):
        self.assertEqual(self.plan(), guard.PackagePlan((("btop", "1.4.6-2"),), ()))

    def test_invalid_and_prohibited_requests_never_execute_commands(self):
        for name in ("snapd", "snapd:amd64", "flatpak:i386=1.0", "snap", "--allow-unauthenticated",
                     "btop --allow-downgrades", "btop;id", "btop/stable", "./thing.deb", "btop=", "btop:any",
                     "linux-image-generic", "cryptsetup", "lvm2", "grub-common", "initramfs-tools", "dkms"):
            with self.subTest(name=name), patch.object(guard.subprocess, "run") as runner:
                with self.assertRaises(RuntimeError):
                    guard.validate_request(guard.PackageRequest((name,), "ubuntu"))
                runner.assert_not_called()
        for request in (guard.PackageRequest(("btop",), "ppa"), guard.PackageRequest((), "ubuntu"),
                        guard.PackageRequest(["btop"], "ubuntu")):
            with self.subTest(request=request), self.assertRaises(RuntimeError):
                guard.validate_request(request)

    def test_unreviewed_packages_versions_architectures_and_duplicate_selections_block(self):
        for names in (("btop",), ("btop=99",), ("btop:arm64",), ("btop", "btop:amd64")):
            with self.subTest(names=names), patch.object(guard, "_REVIEWS", () if names == ("btop",) else (self.review(),)):
                with self.assertRaises(RuntimeError):
                    guard.validate_request(guard.PackageRequest(names, "ubuntu"))

    def test_review_requires_native_scripts_triggers_hooks_paths_and_baseline(self):
        for changes in (dict(native=False), dict(scripts_reviewed=False), dict(triggers_reviewed=False),
                        dict(apt_hooks_reviewed=False), dict(evidence=""), dict(paths=("/boot/initrd.img",)),
                        dict(paths=("/etc/fstab",)), dict(paths=("/usr/share/initramfs-tools/hooks/tool",)),
                        dict(paths=("/etc/crypttab",)), dict(paths=("/usr/lib/modules/x",))):
            with self.subTest(changes=changes), self.assertRaises(RuntimeError):
                self.plan(reviews=(self.review(**changes),))
        with self.assertRaisesRegex(RuntimeError, "baseline"):
            self.plan(baseline="c" * 64)

    def test_transitive_prohibitions_and_protected_changes_block(self):
        for name in ("snapd:amd64", "flatpak", "linux-image-t2", "cryptsetup-bin", "lvm2", "grub-pc", "dkms"):
            simulation = ("0 upgraded, 1 newly installed, 0 to remove and 0 not upgraded.\n"
                          f"Inst {name} (1 Ubuntu:26.04/resolute [amd64])\n"
                          f"Conf {name} (1 Ubuntu:26.04/resolute [amd64])\n")
            with self.subTest(name=name), self.assertRaises(RuntimeError):
                self.plan(simulation)

    def test_transition_fixture_is_rejected_despite_native_origin(self):
        transition = self.review(package="chromium-browser", native=False,
                                 evidence="fixture review: postinst delegates to snap")
        with patch.object(guard, "_REVIEWS", (transition,)):
            with self.assertRaisesRegex(RuntimeError, "review|native|delegat"):
                guard.validate_request(guard.PackageRequest(("chromium-browser",), "ubuntu"))

    def test_unknown_output_removals_missing_configuration_and_inconsistent_counts_block(self):
        for simulation in ("", "surprising output\n", "Remv btop [1]\n",
                           "0 upgraded, 0 newly installed, 1 to remove and 0 not upgraded.\n",
                           "0 upgraded, 1 newly installed, 0 to remove and 0 not upgraded.\n",
                           "0 upgraded, 1 newly installed, 0 to remove and 0 not upgraded.\nInst btop (1.4.6-2 Ubuntu:26.04/resolute [amd64])\n",
                           "0 upgraded, 0 newly installed, 0 to remove and 0 not upgraded.\nInst btop (1.4.6-2 Ubuntu:26.04/resolute [amd64])\nConf btop (1.4.6-2 Ubuntu:26.04/resolute [amd64])\n"):
            with self.subTest(simulation=simulation), self.assertRaises(RuntimeError):
                self.plan(simulation)

    def test_unknown_source_metadata_digest_and_wrong_version_block(self):
        for metadata in ("Package: btop\n", "Package: btop\nVersion: 1.4.6-2\nArchitecture: amd64\nOrigin: PPA\nSHA256: " + "a" * 64 + "\n",
                         "Package: btop\nVersion: 1.4.6-2\nArchitecture: amd64\nOrigin: Ubuntu\nSHA256: " + "c" * 64 + "\n"):
            with self.subTest(metadata=metadata), self.assertRaises(RuntimeError):
                self.plan(metadata=metadata)

    def test_apt_errors_warnings_and_timeout_are_not_success(self):
        with patch.object(guard, "_REVIEWS", (self.review(),)):
            for result in (subprocess.CompletedProcess([], 100, "", "unmet dependencies"),
                           subprocess.CompletedProcess([], 0, "", "warning")):
                with patch.object(guard.subprocess, "run", return_value=result), self.assertRaises(RuntimeError):
                    guard.inspect_plan(guard.PackageRequest(("btop",), "ubuntu"))
            with patch.object(guard.subprocess, "run", side_effect=subprocess.TimeoutExpired("apt-get", 30)), self.assertRaises(RuntimeError):
                guard.inspect_plan(guard.PackageRequest(("btop",), "ubuntu"))

    def test_satisfied_package_still_requires_verified_native_content(self):
        plan = self.plan("btop is already the newest version (1.4.6-2).\n"
                         "0 upgraded, 0 newly installed, 0 to remove and 0 not upgraded.\n")
        self.assertEqual(plan, guard.PackagePlan((), ()))
        with self.assertRaises(RuntimeError):
            self.plan("btop is already the newest version (99).\n"
                      "0 upgraded, 0 newly installed, 0 to remove and 0 not upgraded.\n")

    def test_upgrade_retains_selected_version(self):
        self.assertEqual(self.plan("1 upgraded, 0 newly installed, 0 to remove and 0 not upgraded.\n"
                                   "Inst btop [1.0-1] (1.4.6-2 Ubuntu:26.04/resolute [amd64])\n"
                                   "Conf btop (1.4.6-2 Ubuntu:26.04/resolute [amd64])\n").installs,
                         (("btop", "1.4.6-2"),))

    def test_foreign_simulation_source_and_unreviewed_transitive_package_block(self):
        for name, origin in (("btop", "Vendor:stable"), ("other-native-tool", "Ubuntu:26.04/resolute")):
            with self.subTest(name=name, origin=origin), self.assertRaises(RuntimeError):
                self.plan("0 upgraded, 1 newly installed, 0 to remove and 0 not upgraded.\n"
                          f"Inst {name} (1.4.6-2 {origin} [amd64])\n"
                          f"Conf {name} (1.4.6-2 {origin} [amd64])\n")

    def test_inherited_apt_configuration_is_not_forwarded_and_baseline_changes_block(self):
        review = self.review()
        simulation = ("btop is already the newest version (1.4.6-2).\n"
                      "0 upgraded, 0 newly installed, 0 to remove and 0 not upgraded.\n")
        metadata = "Package: btop\nVersion: 1.4.6-2\nArchitecture: amd64\nOrigin: Ubuntu\nSHA256: " + "a" * 64 + "\n"
        def run(argv, **kwargs):
            self.assertEqual(set(kwargs["env"]), {"PATH", "LC_ALL", "LANG"})
            return subprocess.CompletedProcess(argv, 0, simulation if argv[0].endswith("apt-get") else metadata, "")
        with patch.object(guard, "_REVIEWS", (review,)), \
             patch.object(guard, "_baseline_digest", side_effect=("b" * 64, "c" * 64)), \
             patch.object(guard.subprocess, "run", side_effect=run), \
             patch.dict("os.environ", {"APT_CONFIG": "/tmp/foreign.conf", "BASH_ENV": "/tmp/foreign.sh"}):
            with self.assertRaisesRegex(RuntimeError, "baseline changed"):
                guard.inspect_plan(guard.PackageRequest(("btop",), "ubuntu"))

    def test_baseline_binds_scripts_apt_hooks_and_pending_trigger_state(self):
        from pathlib import Path
        import tempfile
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for directory in ("var/lib/dpkg/info", "var/lib/dpkg/triggers", "var/lib/dpkg/updates", "etc/apt"):
                (root / directory).mkdir(parents=True, exist_ok=True)
            (root / "var/lib/dpkg/status").write_text("Status: install ok installed\n")
            script = root / "var/lib/dpkg/info/tool.postinst"
            script.write_text("reviewed script")
            config = root / "etc/apt/apt.conf"
            config.write_text("reviewed apt hooks")
            unincorp = root / "var/lib/dpkg/triggers/Unincorp"
            unincorp.write_text("")
            with patch.object(guard, "Path", side_effect=lambda path: root / str(path).lstrip("/")):
                first = guard._baseline_digest()
                preferences = root / "etc/apt/preferences.d"
                preferences.mkdir()
                (preferences / "90-t2-package-policy.pref").write_text("Package: snapd flatpak\nPin: version *\nPin-Priority: -1\n")
                self.assertEqual(first, guard._baseline_digest())
                script.write_text("changed script")
                self.assertNotEqual(first, guard._baseline_digest())
                second = guard._baseline_digest()
                config.write_text("changed apt hook configuration")
                self.assertNotEqual(second, guard._baseline_digest())
                unincorp.write_text("pending trigger")
                with self.assertRaisesRegex(RuntimeError, "Pending dpkg triggers"):
                    guard._baseline_digest()
                unincorp.write_text("")
                (root / "var/lib/dpkg/status").write_text("Status: install ok triggers-pending\n")
                with self.assertRaisesRegex(RuntimeError, "Pending dpkg triggers"):
                    guard._baseline_digest()
                (root / "var/lib/dpkg/status").write_text("Status: install ok installed\n")
                (root / "var/lib/dpkg/updates/0000").write_text("pending update")
                with self.assertRaisesRegex(RuntimeError, "Pending dpkg updates"):
                    guard._baseline_digest()
                (root / "var/lib/dpkg/updates/0000").unlink()
                script.unlink()
                script.symlink_to(config)
                with self.assertRaisesRegex(RuntimeError, "Unrecognized"):
                    guard._baseline_digest()


    def test_exact_architecture_and_version_selection_pass_unchanged_to_simulation(self):
        self.assertEqual(self.plan(request=guard.PackageRequest(("btop:amd64=1.4.6-2",), "ubuntu")).installs,
                         (("btop", "1.4.6-2"),))

    def test_reviewed_native_transitive_plan_passes_with_every_dependency_version_retained(self):
        reviews = (self.review(), self.review(package="libfixture", version="2.0-1", paths=("/usr/lib/libfixture.so",)))
        output = ("0 upgraded, 2 newly installed, 0 to remove and 0 not upgraded.\n"
                  "Inst libfixture (2.0-1 Ubuntu:26.04/resolute [amd64])\n"
                  "Inst btop (1.4.6-2 Ubuntu:26.04/resolute [amd64])\n"
                  "Conf libfixture (2.0-1 Ubuntu:26.04/resolute [amd64])\n"
                  "Conf btop (1.4.6-2 Ubuntu:26.04/resolute [amd64])\n")
        def run(argv, **kwargs):
            if argv[0].endswith("apt-get"):
                return subprocess.CompletedProcess(argv, 0, output, "")
            name, version = argv[-1].split("=")
            name = name.split(":")[0]
            metadata = f"Package: {name}\nVersion: {version}\nArchitecture: amd64\nOrigin: Ubuntu\nSHA256: " + "a" * 64 + "\n"
            return subprocess.CompletedProcess(argv, 0, metadata, "")
        with patch.object(guard, "_REVIEWS", reviews), patch.object(guard, "_baseline_digest", return_value="b" * 64), \
             patch.object(guard.subprocess, "run", side_effect=run):
            self.assertEqual(guard.inspect_plan(guard.PackageRequest(("btop",), "ubuntu")).installs,
                             (("libfixture", "2.0-1"), ("btop", "1.4.6-2")))

    def reviewed_fixture_plan(self, names, requested=None, reviews=None):
        """Every fixture resolution has complete review, isolating hard boundaries."""
        reviews = reviews or tuple(self.review(package=name, paths=(f"/usr/bin/{name}",)) for name in names)
        output = f"0 upgraded, {len(names)} newly installed, 0 to remove and 0 not upgraded.\n"
        output += "".join(f"{action} {name} (1.4.6-2 Ubuntu:26.04/resolute [amd64])\n"
                          for action in ("Inst", "Conf") for name in names)
        def run(argv, **kwargs):
            if argv[0].endswith("apt-get"):
                return subprocess.CompletedProcess(argv, 0, output, "")
            name = argv[-1].split("=")[0].split(":")[0]
            metadata = (f"Package: {name}\nVersion: 1.4.6-2\nArchitecture: amd64\nOrigin: Ubuntu\n"
                        "SHA256: " + "a" * 64 + "\n")
            return subprocess.CompletedProcess(argv, 0, metadata, "")
        with patch.object(guard, "_REVIEWS", reviews), \
             patch.object(guard, "_baseline_digest", return_value="b" * 64), \
             patch.object(guard.subprocess, "run", side_effect=run):
            return guard.inspect_plan(guard.PackageRequest(requested or tuple(names), "ubuntu"))

    def test_review_cannot_authorize_protected_storage_libraries(self):
        for name in ("libcryptsetup12", "libdevmapper1.02.1", "libdevmapper-event1.02.1", "liblvm2cmd2.03"):
            for request in ((name,), (name + ":amd64=1.4.6-2",), ("btop",)):
                with self.subTest(name=name, request=request), self.assertRaisesRegex(RuntimeError, "protected package"):
                    self.reviewed_fixture_plan(("btop", name), requested=request)

    def test_review_cannot_authorize_protected_library_or_generator_payloads(self):
        paths = ("/usr/lib/x86_64-linux-gnu/libcryptsetup.so.12.10.0",
                 "/lib/x86_64-linux-gnu/libdevmapper.so.1.02.1",
                 "/usr/lib/aarch64-linux-gnu/libdevmapper-event.so.1.02.1",
                 "/usr/lib/liblvm2cmd.so.2.03", "/usr/lib/initramfs-tools/hooks/fixture",
                 "/usr/share/mkinitcpio/hooks/fixture", "/usr/lib/initcpio/install/fixture",
                 "/usr/lib/mkinitcpio/hooks/fixture", "/usr/lib/grub/x86_64-efi/fixture.mod",
                 "/usr/share/grub/grub-mkconfig_lib", "/usr/lib/systemd/boot/efi/systemd-bootx64.efi",
                 "/usr/bin/bootctl", "/usr/bin/mkinitcpio", "/sbin/update-initramfs",
                 "/bin/mkinitcpio", "/etc/mkinitcpio.conf", "/usr/lib64/libcryptsetup.so.12",
                 "/usr/lib/shim/shimx64.efi", "/usr/bin/efibootmgr", "/usr/bin/grub-mkconfig")
        for path in paths:
            with self.subTest(path=path), self.assertRaisesRegex(RuntimeError, "protected.*path"):
                self.reviewed_fixture_plan(("btop",), reviews=(self.review(paths=(path,)),))

    def test_reviewed_systemd_zram_generator_is_permitted_without_exempting_core(self):
        name = "systemd-zram-generator"
        review = self.review(package=name, paths=("/usr/lib/systemd/system-generators/zram-generator",))
        self.assertEqual(self.reviewed_fixture_plan((name,), reviews=(review,)).installs, ((name, "1.4.6-2"),))
        for changes in (dict(native=False), dict(scripts_reviewed=False), dict(triggers_reviewed=False),
                        dict(apt_hooks_reviewed=False), dict(paths=("/boot/initrd.img",))):
            with self.subTest(changes=changes), self.assertRaises(RuntimeError):
                self.reviewed_fixture_plan((name,), reviews=(dataclasses.replace(review, **changes),))
        for core in ("systemd", "systemd-boot", "systemd-cryptsetup", "systemd-ukify",
                     "systemd-zram-generator-extra", "efibootmgr", "bootctl", "ukify"):
            with self.subTest(core=core), self.assertRaisesRegex(RuntimeError, "protected package"):
                self.reviewed_fixture_plan((core,))

    def test_double_root_payload_paths_cannot_hide_protected_targets(self):
        for path in ("//boot/initrd.img", "//etc/fstab", "//usr/lib/initramfs-tools/hooks/fixture",
                     "//usr/lib/x86_64-linux-gnu/libcryptsetup.so.12"):
            with self.subTest(path=path), self.assertRaisesRegex(RuntimeError, "protected|unrecognized|canonical"):
                self.reviewed_fixture_plan(("btop",), reviews=(self.review(paths=(path,)),))

    def test_additional_review_state_requires_canonical_single_root_paths(self):
        for path in ("//etc/apt/apt.conf", "//usr/lib/fixture-hook", "/etc/apt/../apt/apt.conf",
                     "/etc//apt/apt.conf", "/etc/apt/./apt.conf", "relative-hook"):
            with self.subTest(path=path), self.assertRaisesRegex(RuntimeError, "baseline|canonical|unrecognized"):
                self.reviewed_fixture_plan(("btop",), reviews=(self.review(additional_state_paths=(path,)),))
