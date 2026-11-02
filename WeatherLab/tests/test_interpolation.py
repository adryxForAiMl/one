import unittest

from backend.exceptions import ValidationError
from backend.interpolation import (
    lagrange_interpolation, newton_divided_differences, newton_forward, newton_backward,
)


class InterpolationTests(unittest.TestCase):
    def test_recovers_linear_value(self):
        self.assertAlmostEqual(lagrange_interpolation([0, 1, 2], [1, 3, 5], 1.5), 4)

    def test_newton_methods_match_polynomial(self):
        xs, ys = [0, 1, 2, 3], [1, 2, 5, 10]
        for method in (newton_divided_differences, newton_forward, newton_backward):
            self.assertAlmostEqual(method(xs, ys, 1.5), 3.25, places=12)

    def test_rejects_duplicate_abscissas(self):
        with self.assertRaises(ValidationError):
            newton_divided_differences([0, 1, 1], [0, 1, 2], 0.5)

    def test_forward_rejects_nonuniform_spacing(self):
        with self.assertRaises(ValidationError):
            newton_forward([0, 1, 3], [1, 2, 4], 2)
