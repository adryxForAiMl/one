"""Piecewise linear spline interpolation."""
from bisect import bisect_right
from collections.abc import Sequence
from .exceptions import ValidationError
from .validators import validate_finite, validate_xy


def linear_spline(xs: Sequence[float], ys: Sequence[float], target: float) -> float:
    xs, ys = validate_xy(xs, ys, minimum=2)
    target = validate_finite([target], "Target X")[0]
    if xs != sorted(xs) or len(set(xs)) != len(xs):
        raise ValidationError("X values must be strictly increasing for a spline.")
    if target < xs[0] or target > xs[-1]:
        raise ValidationError("Spline target must lie within the data range.")
    i = min(bisect_right(xs, target) - 1, len(xs) - 2)
    return ys[i] + (ys[i + 1] - ys[i]) * (target - xs[i]) / (xs[i + 1] - xs[i])


def natural_cubic_spline(xs: Sequence[float], ys: Sequence[float], target: float) -> float:
    """Evaluate a natural cubic spline with zero endpoint curvature."""
    xs, ys = validate_xy(xs, ys, minimum=2)
    target = validate_finite([target], "Target X")[0]
    if xs != sorted(xs) or len(set(xs)) != len(xs):
        raise ValidationError("X values must be strictly increasing for a spline.")
    if target < xs[0] or target > xs[-1]:
        raise ValidationError("Spline target must lie within the data range.")
    n = len(xs)
    second = [0.0] * n
    if n > 2:
        widths = [xs[i + 1] - xs[i] for i in range(n - 1)]
        lower, diag, upper, rhs = [], [], [], []
        for i in range(1, n - 1):
            lower.append(widths[i - 1])
            diag.append(2 * (widths[i - 1] + widths[i]))
            upper.append(widths[i])
            rhs.append(6 * ((ys[i + 1] - ys[i]) / widths[i] - (ys[i] - ys[i - 1]) / widths[i - 1]))
        for i in range(1, len(diag)):
            factor = lower[i] / diag[i - 1]
            diag[i] -= factor * upper[i - 1]
            rhs[i] -= factor * rhs[i - 1]
        inner = [0.0] * len(diag)
        inner[-1] = rhs[-1] / diag[-1]
        for i in range(len(inner) - 2, -1, -1):
            inner[i] = (rhs[i] - upper[i] * inner[i + 1]) / diag[i]
        second[1:-1] = inner
    i = min(bisect_right(xs, target) - 1, n - 2)
    width = xs[i + 1] - xs[i]
    left, right = (xs[i + 1] - target) / width, (target - xs[i]) / width
    return (left * ys[i] + right * ys[i + 1]
            + ((left**3 - left) * second[i] + (right**3 - right) * second[i + 1]) * width**2 / 6)
