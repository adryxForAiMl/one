import unittest

from backend.exceptions import ValidationError
from backend.spline import linear_spline, natural_cubic_spline


class SplineTests(unittest.TestCase):
    def test_splines_pass_through_knots(self):
        xs, ys = [0, 1, 2, 3], [0, 1, 0, 1]
        for spline in (linear_spline, natural_cubic_spline):
            for x, y in zip(xs, ys):
                self.assertAlmostEqual(spline(xs, ys, x), y)

    def test_rejects_unordered_data_and_extrapolation(self):
        with self.assertRaises(ValidationError):
            natural_cubic_spline([0, 2, 1], [0, 2, 1], .5)
        with self.assertRaises(ValidationError):
            linear_spline([0, 1], [0, 1], 2)
