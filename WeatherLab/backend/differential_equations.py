"""Initial value problem solvers for y' = f(x, y)."""
from dataclasses import dataclass
import math
from collections.abc import Callable

from .exceptions import ValidationError


@dataclass
class ODESolution:
    x_values: list[float]
    y_values: list[float]
    step_size: float

    def __iter__(self):
        yield self.x_values
        yield self.y_values


def solve_ivp(function: Callable[[float, float], float], x0: float, y0: float,
              x_end: float, steps: int = 100, method: str = "rk4",
              step_size: float | None = None) -> ODESolution:
    """Solve an IVP using Euler, improved Euler (Heun), or RK4."""
    if not all(math.isfinite(v) for v in (x0, y0, x_end)) or x0 == x_end:
        raise ValidationError("Initial values and end point must be finite, with a nonzero interval.")
    method = method.lower().replace("runge-kutta 4", "rk4").replace("runge-kutta", "rk4")
    if method not in ("euler", "heun", "rk4"):
        raise ValidationError("Method must be Euler, Heun, or RK4.")
    if step_size is not None:
        if not math.isfinite(step_size) or step_size <= 0:
            raise ValidationError("Step size must be positive and finite.")
        steps = max(1, math.ceil(abs(x_end - x0) / step_size))
    if not isinstance(steps, int) or steps < 1:
        raise ValidationError("Steps must be a positive integer.")
    if steps > 5000:
        raise ValidationError("Interactive ODE solves are limited to 5000 steps.")
    h = (x_end - x0) / steps
    xs, ys = [x0], [y0]
    x, y = x0, y0
    for _ in range(steps):
        if method == "euler":
            y += h * function(x, y)
        elif method == "heun":
            k1 = function(x, y)
            predictor = y + h * k1
            k2 = function(x + h, predictor)
            y += h * (k1 + k2) / 2
        elif method == "rk4":
            k1 = function(x, y)
            k2 = function(x + h / 2, y + h * k1 / 2)
            k3 = function(x + h / 2, y + h * k2 / 2)
            k4 = function(x + h, y + h * k3)
            y += h * (k1 + 2 * k2 + 2 * k3 + k4) / 6
        else:
            raise ValidationError("Method must be 'euler' or 'rk4'.")
        x += h
        if not math.isfinite(x) or not math.isfinite(y):
            raise ValidationError("ODE solution became non-finite; check the function or step size.")
        xs.append(x)
        ys.append(y)
    return ODESolution(xs, ys, h)
