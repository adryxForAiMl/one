"""Unit tests for numerical methods: Trapezoidal rule, Richardson error, Least-squares, and PGD."""

import pytest
import numpy as np
from Traffic.backend.numerical_methods import (
    trapezoidal_rule,
    trapezoidal_cumulative,
    estimate_trapezoidal_error,
    least_squares_linear,
    project_onto_simplex_with_bounds,
    projected_gradient_descent
)


def test_trapezoidal_rule_quadratic():
    """Verify \int_0^3 x^2 dx = 9.0 using fine discretization."""
    x = np.linspace(0.0, 3.0, 1000)
    y = x ** 2
    integral = trapezoidal_rule(y, x)
    assert abs(integral - 9.0) < 1e-4


def test_trapezoidal_rule_sine():
    """Verify \int_0^\pi \sin(x) dx = 2.0."""
    x = np.linspace(0.0, np.pi, 500)
    y = np.sin(x)
    integral = trapezoidal_rule(y, x)
    assert abs(integral - 2.0) < 1e-4


def test_trapezoidal_cumulative():
    """Verify cumulative trapezoidal integration matches running area."""
    x = np.array([0.0, 1.0, 2.0, 3.0])
    y = np.array([2.0, 2.0, 2.0, 2.0])  # Rectangular constant function
    cum = trapezoidal_cumulative(y, x)
    expected = np.array([0.0, 2.0, 4.0, 6.0])
    np.testing.assert_allclose(cum, expected, atol=1e-6)


def test_estimate_trapezoidal_error():
    """Richardson error estimate on polynomial."""
    x_fine = np.linspace(0.0, 2.0, 101)
    x_coarse = x_fine[::2]
    y_fine = x_fine ** 3
    y_coarse = x_coarse ** 3
    
    i_fine = trapezoidal_rule(y_fine, x_fine)
    i_coarse = trapezoidal_rule(y_coarse, x_coarse)
    err = estimate_trapezoidal_error(i_fine, i_coarse)
    
    exact = 4.0  # \int_0^2 x^3 dx = 4.0
    actual_err = abs(i_fine - exact)
    # Richardson error estimate should closely mirror actual error
    assert err < 0.01
    assert abs(err - actual_err) < 1e-3


def test_least_squares_linear_calibration():
    """Test parameter estimation on synthetic linear queue discharge data."""
    true_slope = 0.50     # 0.50 veh/sec
    true_intercept = 10.0 # 10 initial vehicles
    
    x = np.linspace(0, 20, 21)
    np.random.seed(42)
    noise = np.random.normal(0, 0.05, size=len(x))
    y = true_slope * x + true_intercept + noise
    
    res = least_squares_linear(x, y)
    assert abs(res.slope - true_slope) < 0.02
    assert abs(res.intercept - true_intercept) < 0.15
    assert res.r_squared > 0.98


def test_project_onto_simplex_with_bounds():
    """Test projection of arbitrary vector onto hyperplane \sum x_i = C with box bounds."""
    x = np.array([10.0, 80.0, 5.0])
    target_sum = 60.0
    lb = np.array([10.0, 10.0, 10.0])
    ub = np.array([50.0, 50.0, 50.0])
    
    projected = project_onto_simplex_with_bounds(x, target_sum, lb, ub)
    
    assert abs(np.sum(projected) - target_sum) < 1e-5
    assert np.all(projected >= lb - 1e-6)
    assert np.all(projected <= ub + 1e-6)


def test_projected_gradient_descent_convergence():
    """Verify convergence of PGD on quadratic convex objective with simplex constraints."""
    # min (x_1 - 25)^2 + (x_2 - 45)^2 s.t. x_1 + x_2 = 70, 10 <= x_i <= 60
    def cost_fn(x):
        return float((x[0] - 25.0)**2 + (x[1] - 45.0)**2)
        
    def grad_fn(x):
        return np.array([2.0 * (x[0] - 25.0), 2.0 * (x[1] - 45.0)])
        
    x0 = np.array([35.0, 35.0])
    lb = np.array([10.0, 10.0])
    ub = np.array([60.0, 60.0])
    
    trace = projected_gradient_descent(
        cost_function=cost_fn,
        gradient_function=grad_fn,
        x0=x0,
        lower_bounds=lb,
        upper_bounds=ub,
        target_sum=70.0,
        learning_rate=0.2,
        max_iterations=50
    )
    
    assert trace.converged
    np.testing.assert_allclose(trace.solution, [25.0, 45.0], atol=1e-2)
    assert abs(trace.final_objective - 0.0) < 1e-3
