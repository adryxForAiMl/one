"""Composite numerical integration rules."""
import math
from collections.abc import Callable

from .exceptions import ValidationError


def _validate_interval(a: float, b: float, intervals: int, minimum: int) -> None:
    if not math.isfinite(a) or not math.isfinite(b) or a == b:
        raise ValidationError("Integration bounds must be finite and different.")
    if not isinstance(intervals, int) or intervals < minimum:
        raise ValidationError(f"This rule requires at least {minimum} integer subintervals.")


def _finite_result(value: float) -> float:
    if not math.isfinite(value):
        raise ValidationError("Integration produced a non-finite result.")
    return value


def trapezoidal(function: Callable[[float], float], a: float, b: float,
                intervals: int = 100) -> float:
    _validate_interval(a, b, intervals, 1)
    h = (b - a) / intervals
    return _finite_result(h * (0.5 * function(a) + sum(function(a + i * h) for i in range(1, intervals)) + 0.5 * function(b)))


def simpson(function: Callable[[float], float], a: float, b: float,
            intervals: int = 100) -> float:
    if intervals % 2:
        raise ValidationError("Simpson's 1/3 rule requires an even number of subintervals.")
    _validate_interval(a, b, intervals, 2)
    h = (b - a) / intervals
    total = function(a) + function(b)
    total += 4 * sum(function(a + i * h) for i in range(1, intervals, 2))
    total += 2 * sum(function(a + i * h) for i in range(2, intervals, 2))
    return _finite_result(total * h / 3)


def simpson_three_eighths(function: Callable[[float], float], a: float, b: float,
                         intervals: int = 99) -> float:
    """Composite Simpson 3/8 rule; interval count must be divisible by 3."""
    _validate_interval(a, b, intervals, 3)
    if intervals % 3:
        raise ValidationError("Simpson's 3/8 rule requires an interval count divisible by 3.")
    h = (b - a) / intervals
    total = function(a) + function(b)
    total += 3 * sum(function(a + i * h) for i in range(1, intervals) if i % 3)
    total += 2 * sum(function(a + i * h) for i in range(3, intervals, 3))
    return _finite_result(3 * h * total / 8)
