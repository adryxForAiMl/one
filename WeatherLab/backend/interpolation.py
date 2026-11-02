"""Polynomial interpolation methods."""

import math
from collections.abc import Sequence

from .exceptions import ValidationError
from .validators import validate_finite, validate_xy


def lagrange_interpolation(xs: Sequence[float], ys: Sequence[float], target: float) -> float:
    """Evaluate the Lagrange interpolating polynomial at ``target``."""
    xs, ys = validate_xy(xs, ys, minimum=2)
    target = validate_finite([target], "Target X")[0]
    if len(set(xs)) != len(xs):
        raise ValidationError("X values must be unique.")

    total = 0.0
    for i, yi in enumerate(ys):
        term = yi
        for j, xj in enumerate(xs):
            if i != j:
                term *= (target - xj) / (xs[i] - xj)
        total += term
    if not math.isfinite(total):
        raise ValidationError("Interpolation produced a non-finite estimate.")
    return total


def newton_divided_differences(xs: Sequence[float], ys: Sequence[float], target: float) -> float:
    """Evaluate Newton's divided-difference interpolating polynomial."""
    xs, coefficients = _divided_difference_coefficients(xs, ys)
    target = validate_finite([target], "Target X")[0]
    value = coefficients[-1]
    for index in range(len(coefficients) - 2, -1, -1):
        value = coefficients[index] + (target - xs[index]) * value
    if not math.isfinite(value):
        raise ValidationError("Interpolation produced a non-finite estimate.")
    return value


def divided_difference_coefficients(xs: Sequence[float], ys: Sequence[float]) -> list[float]:
    """Return Newton divided-difference coefficients for the supplied points."""
    return _divided_difference_coefficients(xs, ys)[1]


def _divided_difference_coefficients(xs: Sequence[float], ys: Sequence[float]) -> tuple[list[float], list[float]]:
    xs, ys = validate_xy(xs, ys, minimum=2)
    if len(set(xs)) != len(xs):
        raise ValidationError("X values must be unique.")
    coefficients = list(ys)
    for order in range(1, len(xs)):
        for index in range(len(xs) - 1, order - 1, -1):
            coefficients[index] = (coefficients[index] - coefficients[index - 1]) / (xs[index] - xs[index - order])
    return xs, coefficients


def _uniform_step(xs: Sequence[float]) -> tuple[list[float], float]:
    xs, _ = validate_xy(xs, [0.0] * len(xs), minimum=2)
    step = xs[1] - xs[0]
    if step == 0 or not all(math.isclose(xs[i + 1] - xs[i], step, rel_tol=1e-9, abs_tol=1e-12) for i in range(len(xs) - 1)):
        raise ValidationError("Newton forward/backward methods require equally spaced X values.")
    return xs, step


def newton_forward(xs: Sequence[float], ys: Sequence[float], target: float) -> float:
    """Evaluate Newton's forward formula for equally spaced observations."""
    xs, ys = validate_xy(xs, ys, minimum=2)
    xs, step = _uniform_step(xs)
    target = validate_finite([target], "Target X")[0]
    differences = [list(ys)]
    while len(differences[-1]) > 1:
        row = differences[-1]
        differences.append([row[i + 1] - row[i] for i in range(len(row) - 1)])
    u = (target - xs[0]) / step
    term, result = 1.0, differences[0][0]
    for order in range(1, len(differences)):
        term *= (u - order + 1) / order
        result += term * differences[order][0]
    return result


def newton_backward(xs: Sequence[float], ys: Sequence[float], target: float) -> float:
    """Evaluate Newton's backward formula for equally spaced observations."""
    xs, ys = validate_xy(xs, ys, minimum=2)
    xs, step = _uniform_step(xs)
    target = validate_finite([target], "Target X")[0]
    differences = [list(ys)]
    while len(differences[-1]) > 1:
        row = differences[-1]
        differences.append([row[i + 1] - row[i] for i in range(len(row) - 1)])
    u = (target - xs[-1]) / step
    term, result = 1.0, differences[0][-1]
    for order in range(1, len(differences)):
        term *= (u + order - 1) / order
        result += term * differences[order][-1]
    return result
