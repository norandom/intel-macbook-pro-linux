import unittest
from fractions import Fraction
from manage.pixel_snap import conf, snap


class PixelSnapTests(unittest.TestCase):
    def test_snapped_sizes_are_whole_device_pixels(self):
        for scale in ("1.6", "1.5", "1.25", "1.75"):
            for v in (2, 22, 24):
                self.assertEqual((snap(v, scale) * Fraction(scale)).denominator, 1, (scale, v))

    def test_owner_values(self):
        self.assertEqual((snap(2, 1.6), snap(22, 1.6), snap(24, 1.6)), (0, 20, 25))
        self.assertEqual((snap(2, 1.5), snap(22, 1.5)), (2, 22))
        self.assertIn("no snapping", conf("auto"))
        self.assertIn("no snapping", conf(2))
        self.assertIn("bar_height = 20", conf(1.6))


if __name__ == "__main__":
    unittest.main()
