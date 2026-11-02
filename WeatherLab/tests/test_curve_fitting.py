import unittest

from backend.curve_fitting import polynomial_fit
from backend.exceptions import ValidationError


class CurveFittingTests(unittest.TestCase):
    def test_linear_regression_coefficients_and_r_squared(self):
        result = polynomial_fit([0, 1, 2, 3], [1, 3, 5, 7], degree=1)
        self.assertAlmostEqual(result.coefficients[0], 1)
        self.assertAlmostEqual(result.coefficients[1], 2)
        self.assertAlmostEqual(result.r_squared, 1)

    def test_rejects_rank_deficient_data(self):
        with self.assertRaises(ValidationError):
            polynomial_fit([1, 1, 1], [2, 3, 4], degree=1)
