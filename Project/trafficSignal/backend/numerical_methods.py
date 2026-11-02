"""Numerical Analysis methods for traffic signal optimization.

Includes:
1. Composite Trapezoidal Rule for accumulated queue and waiting-time integration.
2. Richardson extrapolation and numerical error estimation.
3. Ordinary Least Squares (OLS) parameter estimation for saturation flow rates.
4. Projected Gradient Descent for constrained green-time allocation.
5. Numerical sensitivity and convergence analysis tools.
"""

from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from typing import Callable, Tuple, List, Dict, Any


@dataclass
class LeastSquaresResult:
    """Statistical summary of Ordinary Least Squares regression."""
    slope: float              # Estimated rate (e.g. saturation flow rate s in veh/s)
    intercept: float          # Offset (e.g. initial queue or lost time offset)
    r_squared: float          # Coefficient of determination R^2
    standard_error: float     # Standard error of the regression estimate
    residuals: np.ndarray     # Residual errors: y - y_pred
    p_value_slope: float      # Approximate p-value for significance


@dataclass
class OptimizationConvergenceTrace:
    """Trace of numerical optimization steps for convergence analysis."""
    iterations: int
    converged: bool
    objective_history: List[float]
    gradient_norm_history: List[float]
    solution: np.ndarray
    final_objective: float
    message: str


def trapezoidal_rule(y: np.ndarray, x: np.ndarray | None = None, dx: float = 1.0) -> float:
    """Compute the definite integral using the Composite Trapezoidal Rule:
        \int_{a}^{b} f(t) dt \approx \sum_{k=0}^{N-1} \frac{f(t_k) + f(t_{k+1})}{2} \Delta t_k

    Args:
        y: Sample values of integrand (e.g. queue length at discrete intervals).
        x: Sample points corresponding to y. If None, uniform spacing dx is assumed.
        dx: Uniform step size when x is not provided.

    Returns:
        float: Approximate definite integral (e.g. total vehicle-seconds of delay).
    """
    y = np.asarray(y, dtype=float)
    if len(y) < 2:
        return 0.0

    if x is None:
        # Uniform grid spacing
        # Integral = dx * (0.5 * y[0] + \sum_{k=1}^{N-2} y[k] + 0.5 * y[-1])
        return float(dx * (0.5 * y[0] + np.sum(y[1:-1]) + 0.5 * y[-1]))
    else:
        x = np.asarray(x, dtype=float)
        if len(x) != len(y):
            raise ValueError(f"x and y must have identical lengths, got {len(x)} and {len(y)}")
        deltas = np.diff(x)
        return float(np.sum(0.5 * (y[:-1] + y[1:]) * deltas))


def trapezoidal_cumulative(y: np.ndarray, x: np.ndarray | None = None, dx: float = 1.0) -> np.ndarray:
    """Compute the running cumulative integral using the Composite Trapezoidal Rule.
    
    Returns:
        np.ndarray: Cumulative accumulated queue / waiting-time array of length len(y).
    """
    y = np.asarray(y, dtype=float)
    n = len(y)
    if n == 0:
        return np.array([], dtype=float)
    if n == 1:
        return np.array([0.0], dtype=float)

    cumulative = np.zeros(n, dtype=float)
    if x is None:
        for k in range(1, n):
            segment = dx * 0.5 * (y[k - 1] + y[k])
            cumulative[k] = cumulative[k - 1] + segment
    else:
        x = np.asarray(x, dtype=float)
        for k in range(1, n):
            delta = x[k] - x[k - 1]
            segment = delta * 0.5 * (y[k - 1] + y[k])
            cumulative[k] = cumulative[k - 1] + segment

    return cumulative


def estimate_trapezoidal_error(integral_fine: float, integral_coarse: float) -> float:
    """Estimate numerical truncation error of the trapezoidal rule via Richardson extrapolation.
    Since trapezoidal rule error is O(h^2):
        E_fine \approx \frac{I_{h/2} - I_h}{3}
    """
    return abs(integral_fine - integral_coarse) / 3.0


def least_squares_linear(x: np.ndarray, y: np.ndarray) -> LeastSquaresResult:
    """Ordinary Least Squares linear regression y = slope * x + intercept.
    Used for calibrating traffic parameters such as saturation flow rate s (veh/sec)
    from empirical cumulative vehicle discharge data.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = len(x)
    if n < 2:
        return LeastSquaresResult(
            slope=0.0, intercept=0.0, r_squared=0.0,
            standard_error=0.0, residuals=np.zeros_like(y), p_value_slope=1.0
        )

    x_mean = np.mean(x)
    y_mean = np.mean(y)

    ss_xx = np.sum((x - x_mean) ** 2)
    ss_xy = np.sum((x - x_mean) * (y - y_mean))
    ss_yy = np.sum((y - y_mean) ** 2)

    if ss_xx < 1e-12:
        slope = 0.0
        intercept = y_mean
    else:
        slope = float(ss_xy / ss_xx)
        intercept = float(y_mean - slope * x_mean)

    y_pred = slope * x + intercept
    residuals = y - y_pred
    ss_res = np.sum(residuals ** 2)

    r_squared = float(1.0 - (ss_res / ss_yy)) if ss_yy > 1e-12 else 1.0
    r_squared = max(0.0, min(1.0, r_squared))

    df = max(1, n - 2)
    s_err = float(np.sqrt(ss_res / df))

    # T-test for slope
    se_slope = s_err / np.sqrt(ss_xx) if ss_xx > 1e-12 else 1.0
    t_stat = abs(slope / se_slope) if se_slope > 1e-12 else 0.0
    # Approximate two-tailed p-value via normal distribution approximation
    from scipy.stats import t as t_dist
    p_val = float(2.0 * (1.0 - t_dist.cdf(t_stat, df=df)))

    return LeastSquaresResult(
        slope=slope,
        intercept=intercept,
        r_squared=r_squared,
        standard_error=s_err,
        residuals=residuals,
        p_value_slope=p_val
    )


def project_onto_simplex_with_bounds(
    x: np.ndarray,
    target_sum: float,
    lower_bounds: np.ndarray,
    upper_bounds: np.ndarray,
    max_iter: int = 100,
    tol: float = 1e-7
) -> np.ndarray:
    """Project vector x onto the bounded hyperplane:
        \sum x_i = target_sum
        lower_bounds_i \le x_i \le upper_bounds_i

    Uses a robust bisection on the Lagrange multiplier lambda for the Karush-Kuhn-Tucker (KKT) system:
        x_i^*(\lambda) = \text{clip}(x_i - \lambda, lower_bounds_i, upper_bounds_i)
        Find \lambda such that \sum x_i^*(\lambda) = target_sum
    """
    x = np.asarray(x, dtype=float)
    lb = np.asarray(lower_bounds, dtype=float)
    ub = np.asarray(upper_bounds, dtype=float)

    # Sanity checks
    min_possible = np.sum(lb)
    max_possible = np.sum(ub)
    if target_sum < min_possible:
        return lb.copy()
    if target_sum > max_possible:
        return ub.copy()

    # Bracket lambda
    low = np.min(x - ub)
    high = np.max(x - lb)

    for _ in range(max_iter):
        mid = 0.5 * (low + high)
        projected = np.clip(x - mid, lb, ub)
        curr_sum = np.sum(projected)

        if abs(curr_sum - target_sum) <= tol:
            return projected

        if curr_sum > target_sum:
            low = mid
        else:
            high = mid

    return np.clip(x - 0.5 * (low + high), lb, ub)


def projected_gradient_descent(
    cost_function: Callable[[np.ndarray], float],
    gradient_function: Callable[[np.ndarray], np.ndarray],
    x0: np.ndarray,
    lower_bounds: np.ndarray,
    upper_bounds: np.ndarray,
    target_sum: float,
    learning_rate: float = 0.2,
    max_iterations: int = 120,
    tolerance: float = 1e-5
) -> OptimizationConvergenceTrace:
    """Constrained optimization of signal green times via Projected Gradient Descent.
    
    Solves:
        \min_{g} J(g)
        s.t. \sum g_i = C_eff
             g_min \le g \le g_max
    
    Tracks full objective trajectory and gradient norm for numerical convergence analysis.
    """
    # Start from projected initial guess
    x = project_onto_simplex_with_bounds(x0, target_sum, lower_bounds, upper_bounds)
    
    obj_history: List[float] = []
    grad_norm_history: List[float] = []
    converged = False
    message = "Maximum iterations reached"

    step_size = learning_rate

    for it in range(max_iterations):
        curr_cost = float(cost_function(x))
        obj_history.append(curr_cost)

        grad = np.asarray(gradient_function(x), dtype=float)
        g_norm = float(np.linalg.norm(grad))
        grad_norm_history.append(g_norm)

        # Gradient step with projection
        x_next = project_onto_simplex_with_bounds(
            x - step_size * grad, target_sum, lower_bounds, upper_bounds
        )

        step_norm = float(np.linalg.norm(x_next - x))
        if step_norm < tolerance:
            converged = True
            message = f"Converged successfully in {it + 1} iterations (step norm {step_norm:.2e} < {tolerance})"
            x = x_next
            break

        # Armijo-style back-tracking if objective increases drastically
        next_cost = float(cost_function(x_next))
        if next_cost > curr_cost + 1e-4:
            step_size *= 0.5  # Decay learning rate
        else:
            x = x_next

    final_cost = float(cost_function(x))
    obj_history.append(final_cost)

    return OptimizationConvergenceTrace(
        iterations=len(obj_history) - 1,
        converged=converged,
        objective_history=obj_history,
        gradient_norm_history=grad_norm_history,
        solution=x,
        final_objective=final_cost,
        message=message
    )


def sensitivity_analysis(
    optimize_fn: Callable[[Dict[str, Any]], np.ndarray],
    base_params: Dict[str, Any],
    param_keys: List[str],
    delta_pct: float = 0.10
) -> Dict[str, Dict[str, Any]]:
    """Perform finite-difference numerical sensitivity analysis:
    Computes \frac{\partial g^*}{\partial \theta} \approx \frac{g^*(\theta + \Delta) - g^*(\theta - \Delta)}{2 \Delta}
    """
    base_sol = optimize_fn(base_params)
    results = {}

    for key in param_keys:
        if key not in base_params:
            continue
        val = base_params[key]
        if not isinstance(val, (int, float)):
            continue

        delta = abs(val * delta_pct) if abs(val) > 1e-6 else delta_pct
        
        params_up = base_params.copy()
        params_up[key] = val + delta
        sol_up = optimize_fn(params_up)

        params_dn = base_params.copy()
        params_dn[key] = max(0.001, val - delta)
        sol_dn = optimize_fn(params_dn)

        derivative = (sol_up - sol_dn) / (2.0 * delta)
        elasticity = (derivative * val) / np.maximum(base_sol, 1e-6)

        results[key] = {
            "parameter": key,
            "nominal_value": val,
            "delta": delta,
            "derivative": derivative.tolist(),
            "elasticity": elasticity.tolist()
        }

    return results
