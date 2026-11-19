"""Sender-side TCP tuning: the sysctl file matches the managed settings (offline)."""
import unittest
from pathlib import Path

from manage import network_tuning as nt

ROOT = Path(__file__).resolve().parents[1]


class NetworkTuning(unittest.TestCase):
    def test_file_sets_exactly_the_managed_settings(self):
        conf = nt.parse((ROOT / "files/network-tuning/61-t2-network.conf").read_text())
        self.assertEqual(conf, {key: managed for key, (managed, _default) in nt.SETTINGS.items()})

    def test_only_sender_side_tcp_no_buffers_or_queue(self):
        for key in nt.SETTINGS:
            self.assertTrue(key.startswith("net.ipv4.tcp_"), key)
        self.assertEqual(nt.SETTINGS["net.ipv4.tcp_congestion_control"], ("bbr", "cubic"))

    def test_verify_and_restore_cover_every_setting(self):
        self.assertEqual(len(nt.verify_commands()), len(nt.SETTINGS))
        self.assertIn("sysctl -w net.ipv4.tcp_congestion_control=cubic", nt.restore_commands())
        self.assertIn('test "$(sysctl -n net.ipv4.tcp_mtu_probing)" = 1', nt.verify_commands())

    def test_wired_into_the_deploy_before_shaping(self):
        deploy = (ROOT / "deploy.py").read_text()
        self.assertLess(deploy.index('"network_tuning"'), deploy.index('"traffic_shaping"'))
        task = (ROOT / "tasks/network_tuning.py").read_text()
        self.assertIn('setting("network_tuning", True)', task)
        self.assertNotIn("modules-load", task.split('"""')[2])


if __name__ == "__main__":
    unittest.main()
