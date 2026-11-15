"""Health evaluation and shell alert display; no smartctl or sudo."""
import importlib.machinery
import importlib.util
import io
import os
from pathlib import Path
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

FILES = Path(__file__).resolve().parents[1] / 'files/storage-health'


def load(name):
    loader = importlib.machinery.SourceFileLoader(name.replace('-', '_'), str(FILES / name))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class EvaluateTests(unittest.TestCase):
    health = load('t2-storage-health')

    def test_healthy_disk_has_no_problems(self):
        ok = dict(critical_warning=0, available_spare=100, available_spare_threshold=99, percentage_used=3,
                  temperature=40, media_errors=0, num_err_log_entries=0)
        self.assertEqual(self.health.evaluate(ok, ok), [])  # Apple: 100% spare, 99% threshold

    def test_spare_drop_is_reported(self):
        self.assertEqual(len(self.health.evaluate(dict(available_spare=98, available_spare_threshold=10),
                                                  dict(available_spare=100))), 1)

    def test_problems_are_reported(self):
        bad = dict(critical_warning=4, available_spare=4, available_spare_threshold=5, percentage_used=85,
                   temperature=80, media_errors=3, num_err_log_entries=0)
        problems = self.health.evaluate(bad, dict(media_errors=1))
        self.assertEqual(len(problems), 5, problems)


class AlertTests(unittest.TestCase):
    def test_pending_alerts_show_until_acknowledged(self):
        with tempfile.TemporaryDirectory() as root:
            alerts = Path(root, 'alerts')
            alerts.mkdir()
            (alerts / '20261115T120000-smartd-1.txt').write_text('SMART Temperature on /dev/nvme0\nhot\n')
            with patch.dict(os.environ, T2_ALERT_DIR=str(alerts), XDG_STATE_HOME=str(Path(root, 'state'))):
                module = load('t2-alerts')
                with patch.object(module, 'failed_units', return_value=[]):
                    out = io.StringIO()
                    with redirect_stdout(out):
                        module.main(['--brief'])
                    self.assertIn('SMART Temperature', out.getvalue())
                    module.main(['ack'])
                    time.sleep(0.01)
                    out = io.StringIO()
                    with redirect_stdout(out):
                        module.main(['--brief'])
                    self.assertEqual(out.getvalue(), '')


if __name__ == '__main__':
    unittest.main()
