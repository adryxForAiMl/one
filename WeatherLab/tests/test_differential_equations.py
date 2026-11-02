import math
import unittest

from backend.differential_equations import solve_ivp


class DifferentialEquationTests(unittest.TestCase):
    def test_rk4_tracks_exponential(self):
        result = solve_ivp(lambda x, y: y, 0, 1, 1, method="rk4", step_size=.01)
        xs, ys = result
        self.assertAlmostEqual(ys[-1], math.e, places=8)
        self.assertAlmostEqual(xs[-1], 1)

    def test_heun_and_euler_integrate_constant_slope(self):
        for method in ("heun", "euler"):
            result = solve_ivp(lambda x, y: 2, 0, 1, 2, method=method, step_size=.1)
            self.assertAlmostEqual(result.y_values[-1], 5)
