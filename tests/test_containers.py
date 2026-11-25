import hashlib
import json
import unittest
from pathlib import Path
from unittest import mock

from manage import containers as c
from manage import nix_tools as nt
from manage import packages as guard

ROOT = Path(__file__).resolve().parents[1]
TASK = (ROOT / "tasks/containers.py").read_text()


class DockerEngineTests(unittest.TestCase):
    def test_keyring_and_source_are_pinned(self):
        key = ROOT / "files/containers/docker-keyring.gpg"
        self.assertEqual(hashlib.sha256(key.read_bytes()).hexdigest(), c.KEYRING_SHA256)
        source = (ROOT / "files/containers/docker.list").read_text()
        self.assertIn("signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] "
                      "https://download.docker.com/linux/ubuntu resolute stable", source)
        self.assertIn("KEYRING_SHA256", TASK)

    def test_engine_not_desktop(self):
        self.assertEqual(c.PACKAGES, ("docker-ce", "docker-ce-cli", "containerd.io",
                                      "docker-buildx-plugin", "docker-compose-plugin"))
        self.assertNotIn("docker-desktop", TASK.replace("Docker Desktop", ""))

    def test_one_transaction_swaps_podman_for_docker(self):
        self.assertIn("schedule_batch(\"Docker Engine\", packages=c.PACKAGES, source_lists=(c.REPO,), replaces=podman_left)", TASK)
        self.assertLessEqual(len(c.PODMAN_PACKAGES), 8)       # PackageRequest.replaces limit
        self.assertIn("podman-docker", c.PODMAN_PACKAGES)      # ships /usr/bin/docker too
        for p in c.PACKAGES + c.PODMAN_PACKAGES:               # nothing the guard refuses
            self.assertFalse(guard._protected(p), p)
        guard.validate_request(guard.PackageRequest(c.PACKAGES, replaces=c.PODMAN_PACKAGES))

    def test_batch_passes_replacements_to_the_root_helper(self):
        with mock.patch("pyinfra.operations.server.shell") as shell:
            guard.schedule_batch("T", packages=("docker-ce",), source_lists=("docker",), replaces=("podman",))
        script = shell.call_args.kwargs["commands"][0]
        self.assertIn("--apply --replace podman docker-ce", script)

    def test_daemon_config(self):
        self.assertTrue(c.DAEMON_CONFIG["ip-forward-no-drop"])        # libvirt NAT keeps working
        self.assertEqual(c.DAEMON_CONFIG["log-opts"], {"max-size": "10m", "max-file": "3"})
        json.dumps(c.DAEMON_CONFIG)
        self.assertIn("dockerd --validate --config-file /etc/docker/daemon.json", TASK)

    def test_socket_activated_and_group(self):
        self.assertIn("systemctl enable docker.socket", TASK)
        self.assertIn("systemctl disable docker.service containerd.service", TASK)
        self.assertIn("usermod -aG docker", TASK)

    def test_podman_leftovers_go(self):
        self.assertIn("rc*) dpkg --purge", TASK)          # profile.d DOCKER_HOST script goes
        for marker in ("podman.socket", "unset-environment DOCKER_HOST", '"podman-tui", "podman-desktop"',
                       "/etc/apparmor.d/t2-podman-desktop"):
            self.assertIn(marker, TASK)
        self.assertNotIn("podman-tui", nt.DEFAULT_TOOLS)
        self.assertIn("lazydocker", nt.DEFAULT_TOOLS)
        self.assertIn("ctop", nt.DEFAULT_TOOLS)

    def test_compose_link_state(self):
        with mock.patch.object(c.Path, "is_symlink", return_value=True), \
             mock.patch.object(c.os, "readlink", return_value=c.OLD_COMPOSE_TARGET):
            self.assertEqual(c.compose_link_state(), "ours")
        with mock.patch.object(c.Path, "is_symlink", return_value=False), \
             mock.patch.object(c.Path, "exists", return_value=False):
            self.assertEqual(c.compose_link_state(), "absent")
        with mock.patch.object(c.Path, "is_symlink", return_value=False), \
             mock.patch.object(c.Path, "exists", return_value=True):
            self.assertEqual(c.compose_link_state(), "foreign")


if __name__ == "__main__":
    unittest.main()
