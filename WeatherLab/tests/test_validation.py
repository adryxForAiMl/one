import unittest
from backend.exceptions import ValidationError
from backend.validators import validate_xy
from utils.helpers import compile_expression


class ValidationTests(unittest.TestCase):
    def test_xy_lengths_must_match(self):
        with self.assertRaises(ValidationError):
            validate_xy([1, 2], [3])

    def test_rejects_non_finite_points(self):
        with self.assertRaises(ValidationError):
            validate_xy([0, float("nan")], [1, 2])

    def test_expression_parser_allows_math_but_rejects_code(self):
        self.assertAlmostEqual(compile_expression("sin(pi/2)")(0), 1)
        with self.assertRaises(ValidationError):
            compile_expression("__import__('os')")(0)

    def test_expression_parser_handles_division_by_zero(self):
        with self.assertRaises(ZeroDivisionError):
            compile_expression("1 / x")(0)
