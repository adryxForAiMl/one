import math
import unittest

from backend.differentiation import derivative
from backend.exceptions import ValidationError


class DifferentiationTests(unittest.TestCase):
    def test_finite_difference_variants(self):
        f = lambda x: x**3
        self.assertAlmostEqual(derivative(f, 2, 1e-3, 1, "central"), 12, places=4)
        self.assertAlmostEqual(derivative(f, 2, 1e-3, 1, "central-5"), 12, places=8)
        self.assertAlmostEqual(derivative(f, 2, 1e-3, 1, "forward"), 12, places=1)
        self.assertAlmostEqual(derivative(f, 2, 1e-3, 1, "backward"), 12, places=1)
        self.assertAlmostEqual(derivative(f, 2, 1e-3, 2, "central-5"), 12, places=5)

    def test_rejects_bad_step(self):
        with self.assertRaises(ValidationError):
            derivative(math.sin, 1, 0)
