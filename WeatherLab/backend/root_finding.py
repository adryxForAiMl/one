"""Scalar root-finding algorithms."""
import math
from collections.abc import Callable
from .exceptions import ValidationError
from .results import IterationResult


def _check_controls(tolerance: float, max_iterations: int) -> None:
    if not math.isfinite(tolerance) or tolerance <= 0 or max_iterations < 1:
        raise ValidationError("Tolerance and iteration limit must be positive and finite.")


def bisection(function: Callable[[float], float], a: float, b: float,
              tolerance: float = 1e-8, max_iterations: int = 100) -> IterationResult[float]:
    _check_controls(tolerance, max_iterations)
    fa, fb = function(a), function(b)
    if not all(map(math.isfinite, (fa, fb))) or fa * fb > 0:
        raise ValidationError("The interval endpoints must bracket a root.")
    if abs(fa) <= tolerance:
        return IterationResult(a, 0, abs(fa), True, [(0, a, fa)])
    if abs(fb) <= tolerance:
        return IterationResult(b, 0, abs(fb), True, [(0, b, fb)])
    history = []
    for i in range(1, max_iterations + 1):
        mid = (a + b) / 2
        fm = function(mid)
        if not math.isfinite(fm):
            raise ValidationError("Function returned a non-finite value inside the bracket.")
        history.append((i, mid, fm))
        if abs(fm) <= tolerance or abs(b - a) / 2 <= tolerance:
            return IterationResult(mid, i, abs(fm), True, history)
        if fa * fm < 0:
            b, fb = mid, fm
        else:
            a, fa = mid, fm
    raise ValidationError("Bisection did not converge within the iteration limit.")


def regula_falsi(function: Callable[[float], float], a: float, b: float,
                 tolerance: float = 1e-8, max_iterations: int = 100) -> IterationResult[float]:
    _check_controls(tolerance, max_iterations)
    fa, fb = function(a), function(b)
    if not all(map(math.isfinite, (fa, fb))) or fa * fb > 0:
        raise ValidationError("The interval endpoints must bracket a root.")
    if abs(fa) <= tolerance:
        return IterationResult(a, 0, abs(fa), True, [(0, a, fa)])
    if abs(fb) <= tolerance:
        return IterationResult(b, 0, abs(fb), True, [(0, b, fb)])
    history = []
    for i in range(1, max_iterations + 1):
        if fb == fa:
            raise ValidationError("Cannot continue: endpoint function values are equal.")
        x = (a * fb - b * fa) / (fb - fa)
        fx = function(x)
        if not math.isfinite(fx):
            raise ValidationError("Function returned a non-finite value during iteration.")
        history.append((i, x, fx))
        if abs(fx) <= tolerance:
            return IterationResult(x, i, abs(fx), True, history)
        if fa * fx < 0:
            b, fb = x, fx
        else:
            a, fa = x, fx
    raise ValidationError("Regula Falsi did not converge within the iteration limit.")


def newton_raphson(function: Callable[[float], float], derivative: Callable[[float], float],
                   x: float, tolerance: float = 1e-8,
                   max_iterations: int = 100) -> IterationResult[float]:
    _check_controls(tolerance, max_iterations)
    history = []
    for i in range(1, max_iterations + 1):
        fx, dfx = function(x), derivative(x)
        if not math.isfinite(fx) or not math.isfinite(dfx):
            raise ValidationError("Function or derivative returned a non-finite value.")
        if abs(dfx) < 1e-15:
            raise ValidationError("Derivative is zero near the current estimate.")
        next_x = x - fx / dfx
        next_value = function(next_x)
        if not math.isfinite(next_x) or not math.isfinite(next_value):
            raise ValidationError("Newton-Raphson produced a non-finite iterate.")
        history.append((i, next_x, next_value))
        if abs(next_x - x) <= tolerance:
            return IterationResult(next_x, i, abs(history[-1][2]), True, history)
        x = next_x
    raise ValidationError("Newton-Raphson did not converge within the iteration limit.")


def secant(function: Callable[[float], float], x0: float, x1: float,
           tolerance: float = 1e-8, max_iterations: int = 100) -> IterationResult[float]:
    """Find a root using the secant method without an explicit derivative."""
    _check_controls(tolerance, max_iterations)
    if not math.isfinite(x0) or not math.isfinite(x1):
        raise ValidationError("Initial guesses must be finite.")
    f0, f1 = function(x0), function(x1)
    if not math.isfinite(f0) or not math.isfinite(f1):
        raise ValidationError("Function returned a non-finite value at an initial guess.")
    history = []
    for iteration in range(1, max_iterations + 1):
        denominator = f1 - f0
        if abs(denominator) < 1e-15:
            raise ValidationError("Secant step failed because function values are equal.")
        x2 = x1 - f1 * (x1 - x0) / denominator
        f2 = function(x2)
        if not math.isfinite(f2):
            raise ValidationError("Function returned a non-finite value during iteration.")
        history.append((iteration, x2, f2))
        if abs(f2) <= tolerance or abs(x2 - x1) <= tolerance:
            return IterationResult(x2, iteration, abs(f2), True, history)
        x0, f0, x1, f1 = x1, f1, x2, f2
    raise ValidationError("Secant method did not converge within the iteration limit.")
