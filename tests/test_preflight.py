"""Fixture-only preflight checks: no host deployment or system mutations."""

import unittest
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

from pyinfra.api import Inventory
from pyinfra.context import ctx_host

from manage.preflight import validate_local_context


class LocalContextTests(unittest.TestCase):
    @contextmanager
    def context(self, *, names=("@local",), current=None, uid=1000,
                euid=1000, system="Linux", release=None, release_error=None):
        inventory = Inventory((list(names), {}))
        selected = inventory.hosts.get(current or names[0]) if names else None
        with ExitStack() as stack:
            stack.enter_context(ctx_host.use(selected))
            stack.enter_context(patch("manage.preflight.os.getuid", return_value=uid))
            stack.enter_context(patch("manage.preflight.os.geteuid", return_value=euid))
            stack.enter_context(patch("manage.preflight.platform.system", return_value=system))
            release_reader = stack.enter_context(patch(
                "manage.preflight.platform.freedesktop_os_release",
                return_value=release if release is not None else {"ID": "ubuntu", "VERSION_ID": "26.04"},
                side_effect=release_error,
            ))
            # Check all contexts under a write/command tripwire. All needed
            # observations are fixtures, so no real OS reads are necessary.
            for target in ("builtins.open", "pathlib.Path.open", "os.open",
                           "os.mkdir", "os.remove", "os.rename", "os.replace",
                           "os.chmod", "os.chown", "os.system", "subprocess.Popen"):
                stack.enter_context(patch(target, side_effect=AssertionError("unexpected I/O")))
            yield release_reader

    def test_unprivileged_local_ubuntu_passes_without_writes(self):
        with self.context():
            self.assertIsNone(validate_local_context())

    def test_root_real_or_effective_user_is_rejected_before_os_inspection(self):
        for uid, euid in ((0, 0), (1000, 0), (0, 1000)):
            with self.subTest(uid=uid, euid=euid), self.context(uid=uid, euid=euid) as reader:
                with self.assertRaisesRegex(RuntimeError, "desktop user.*sudo"):
                    validate_local_context()
                reader.assert_not_called()

    def test_ssh_including_localhost_is_rejected(self):
        for target in ("example.invalid", "localhost", "127.0.0.1"):
            with self.subTest(target=target), self.context(names=(target,)) as reader:
                with self.assertRaisesRegex(RuntimeError, "@local"):
                    validate_local_context()
                reader.assert_not_called()

    def test_mixed_inventory_is_rejected_even_while_processing_local_host(self):
        with self.context(names=("@local", "example.invalid"), current="@local") as reader:
            with self.assertRaisesRegex(RuntimeError, "@local"):
                validate_local_context()
            reader.assert_not_called()

    def test_missing_pyinfra_context_is_rejected(self):
        with self.context(names=()):
            with self.assertRaisesRegex(RuntimeError, "@local"):
                validate_local_context()

    def test_non_linux_is_rejected_without_reading_os_release(self):
        for system in ("Darwin", "Windows", ""):
            with self.subTest(system=system), self.context(system=system) as reader:
                with self.assertRaisesRegex(RuntimeError, "Ubuntu"):
                    validate_local_context()
                reader.assert_not_called()

    def test_non_ubuntu_and_ubuntu_derivatives_are_rejected(self):
        for release in ({"ID": "debian"}, {"ID": "linuxmint", "ID_LIKE": "ubuntu"},
                        {"NAME": "Ubuntu"}, {}):
            with self.subTest(release=release), self.context(release=release):
                with self.assertRaisesRegex(RuntimeError, "Ubuntu"):
                    validate_local_context()

    def test_unreadable_os_identity_fails_with_specific_error(self):
        with self.context(release_error=OSError("fixture: unavailable")):
            with self.assertRaisesRegex(RuntimeError, "verify.*Ubuntu"):
                validate_local_context()

    def test_home_and_remote_user_environment_cannot_override_context(self):
        with self.context(), patch.dict("os.environ", {"HOME": "/root", "USER": "root", "SUDO_USER": "other"}):
            self.assertIsNone(validate_local_context())


if __name__ == "__main__":
    unittest.main()
