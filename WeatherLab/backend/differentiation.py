"""Finite difference differentiation."""
import math
from collections.abc import Callable

from .exceptions import ValidationError


def derivative(function: Callable[[float], float], x: float, step: float = 1e-5,
               order: int = 1, method: str = "central") -> float:
    """Approximate a first or second derivative with finite differences."""
    if not math.isfinite(step) or step <= 0:
        raise ValidationError("Step size must be positive and finite.")
    if not math.isfinite(x):
        raise ValidationError("Evaluation point must be finite.")
    if order not in (1, 2):
        raise ValidationError("Derivative order must be 1 or 2.")
    if method == "forward":
        if order == 1:
            result = (function(x + step) - function(x)) / step
        else:
            result = (function(x + 2 * step) - 2 * function(x + step) + function(x)) / step**2
    elif method == "backward":
        if order == 1:
            result = (function(x) - function(x - step)) / step
        else:
            result = (function(x) - 2 * function(x - step) + function(x - 2 * step)) / step**2
    elif method == "central":
        if order == 1:
            result = (function(x + step) - function(x - step)) / (2 * step)
        else:
            result = (function(x + step) - 2 * function(x) + function(x - step)) / step**2
    elif method == "central-5":
        if order == 1:
            result = (function(x - 2 * step) - 8 * function(x - step)
                      + 8 * function(x + step) - function(x + 2 * step)) / (12 * step)
        else:
            result = (-function(x + 2 * step) + 16 * function(x + step) - 30 * function(x)
                      + 16 * function(x - step) - function(x - 2 * step)) / (12 * step**2)
    else:
        raise ValidationError("Method must be forward, backward, central, or central-5.")
    if not math.isfinite(result):
        raise ValidationError("Differentiation produced a non-finite result.")
    return result
