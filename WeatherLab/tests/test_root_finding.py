import unittest
from backend.exceptions import ValidationError
from backend.root_finding import bisection, newton_raphson, regula_falsi, secant


class RootFindingTests(unittest.TestCase):
    def test_bracketing_methods(self):
        f = lambda x: x * x - 2
        self.assertAlmostEqual(bisection(f, 0, 2)[0], 2 ** .5, places=7)
        self.assertAlmostEqual(regula_falsi(f, 0, 2)[0], 2 ** .5, places=6)

    def test_newton_method(self):
        root, _ = newton_raphson(lambda x: x*x - 2, lambda x: 2*x, 1.5)
        self.assertAlmostEqual(root, 2 ** .5, places=8)

    def test_secant_method_and_metadata(self):
        result = secant(lambda x: x*x - 2, 1, 2)
        self.assertAlmostEqual(result.approximation, 2 ** .5, places=8)
        self.assertTrue(result.converged)
        self.assertLess(result.residual, 1e-8)

    def test_endpoint_root_and_invalid_bracket(self):
        self.assertAlmostEqual(bisection(lambda x: x, 0, 2)[0], 0)
        with self.assertRaises(ValidationError):
            bisection(lambda x: x*x + 1, -1, 1)

    def test_non_convergence_is_reported(self):
        with self.assertRaises(ValidationError):
            bisection(lambda x: x*x - 2, 0, 2, tolerance=1e-30, max_iterations=2)
