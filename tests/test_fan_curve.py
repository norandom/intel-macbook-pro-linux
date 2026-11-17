"""Fan policy tests use a fake sysfs tree; no host writes."""
import importlib.util
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('fan_curve', Path(__file__).resolve().parents[1] / 'files/resource-policy/t2-fan-curve.py')
fc = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fc)


class FanCurveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.hw = self.root / 'hwmon'
        self.smc = self.hw / 'hwmon9'
        self.cpu = self.hw / 'hwmon2'
        self.gpu = self.hw / 'hwmon3'
        for p, name in [(self.smc, 'macsmc_hwmon'), (self.cpu, 'coretemp'), (self.gpu, 'amdgpu')]:
            p.mkdir(parents=True)
            (p / 'name').write_text(name)
        for n, maximum in [(1, 5600), (2, 5200)]:
            for suffix, value in [('min', 1800), ('max', maximum), ('target', 2000), ('input', 2000)]:
                (self.smc / f'fan{n}_{suffix}').write_text(str(value))
        (self.cpu / 'temp1_input').write_text('45000')
        (self.gpu / 'temp1_input').write_text('45000')
        (self.gpu / 'temp1_label').write_text('edge')
        self.param = self.root / 'fan_control'
        self.param.write_text('N')
        self.state = self.root / 'runtime'
        self.state.mkdir()
        self.control = fc.Controller(self.hw, self.param, self.state)

    def test_full_cooling_before_ninety_and_gpu_is_considered(self):
        self.control.start()
        (self.gpu / 'temp1_input').write_text('85000')
        self.control.step()
        self.assertEqual((self.smc / 'fan1_target').read_text(), '5600\n')
        self.assertEqual((self.smc / 'fan2_target').read_text(), '5200\n')
        self.control.restore()
        self.assertEqual((self.smc / 'fan1_target').read_text(), '0\n')
        self.assertEqual(self.param.read_text(), 'N\n')

    def test_auto_at_cool_temperatures_and_hysteresis(self):
        self.control.start()
        self.control.step()
        self.assertEqual((self.smc / 'fan1_target').read_text(), '2000')
        (self.cpu / 'temp1_input').write_text('75000')
        self.control.step()
        self.assertEqual((self.smc / 'fan1_target').read_text(), '4200\n')
        (self.cpu / 'temp1_input').write_text('52000')
        self.control.step()
        self.assertNotEqual((self.smc / 'fan1_target').read_text(), '0\n')
        (self.cpu / 'temp1_input').write_text('49000')
        self.control.step()
        self.assertEqual((self.smc / 'fan1_target').read_text(), '0\n')

    def test_missing_sensor_fails_and_separate_cleanup_restores(self):
        self.control.start()
        (self.cpu / 'temp1_input').write_text('80000')
        self.control.step()
        (self.cpu / 'temp1_input').unlink()
        with self.assertRaises(OSError):
            self.control.step()
        fc.Controller(self.hw, self.param, self.state).restore()
        self.assertEqual(self.param.read_text(), 'N\n')
        self.assertEqual((self.smc / 'fan2_target').read_text(), '0\n')

    def test_does_not_take_over_an_existing_manual_controller(self):
        self.param.write_text('Y')
        with self.assertRaises(RuntimeError):
            self.control.start()
        self.control.restore()
        self.assertEqual(self.param.read_text(), 'Y')
        self.assertEqual((self.smc / 'fan1_target').read_text(), '2000')

    def test_cooling_never_below_initial_firmware_request(self):
        (self.smc / 'fan1_target').write_text('4800')
        self.control.start()
        (self.cpu / 'temp1_input').write_text('60000')
        self.control.step()
        self.assertEqual((self.smc / 'fan1_target').read_text(), '4800\n')

    def test_curve_is_monotonic_and_clamped(self):
        targets = [fc.fan_target(t, 1800, 5600) for t in range(40, 111)]
        self.assertEqual(targets, sorted(targets))
        self.assertTrue(all(1800 <= t <= 5600 for t in targets))
        self.assertEqual(fc.fan_target(85, 1800, 5600), 5600)

    def test_failed_reset_retains_ownership_and_next_start_recovers(self):
        self.control.start()
        (self.cpu / 'temp1_input').write_text('80000')
        self.control.step()
        real_write = fc.write
        def fail_one(path, value):
            if path.name == 'fan1_target' and value == 0:
                raise OSError('temporary SMC failure')
            real_write(path, value)
        with patch.object(fc, 'write', side_effect=fail_one):
            with self.assertRaises(RuntimeError):
                self.control.restore()
        self.assertTrue(self.control.marker.exists())
        self.assertEqual(self.param.read_text(), 'Y\n')
        self.assertEqual((self.smc / 'fan2_target').read_text(), '0\n')
        recovered = fc.Controller(self.hw, self.param, self.state)
        recovered.start()
        recovered.restore()
        self.assertFalse(self.control.marker.exists())
        self.assertEqual(self.param.read_text(), 'N\n')
