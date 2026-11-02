import math
import unittest
from backend.exceptions import ValidationError
from backend.integration import simpson, simpson_three_eighths, trapezoidal


class IntegrationTests(unittest.TestCase):
    def test_simpson_integrates_sine(self):
        self.assertAlmostEqual(simpson(math.sin, 0, math.pi, 100), 2, places=7)

    def test_trapezoidal_integrates_linear_function(self):
        self.assertAlmostEqual(trapezoidal(lambda x: 2*x + 1, 0, 3, 20), 12)

    def test_simpson_three_eighths_exact_for_cubic(self):
        self.assertAlmostEqual(simpson_three_eighths(lambda x: x**3, 0, 2, 6), 4)

    def test_simpson_counts_are_validated(self):
        with self.assertRaises(ValidationError):
            simpson(math.sin, 0, math.pi, 3)
        with self.assertRaises(ValidationError):
            simpson_three_eighths(math.sin, 0, math.pi, 4)
