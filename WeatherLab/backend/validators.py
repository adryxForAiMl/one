"""Shared validation helpers for numerical method inputs."""

import math
from collections.abc import Iterable, Sequence

from .exceptions import ValidationError


def validate_finite(values: Iterable[float], name: str = "values") -> list[float]:
    """Return values as floats, rejecting non-numeric or non-finite entries."""
    try:
        result = [float(value) for value in values]
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{name} must contain numeric values.") from exc
    if not all(math.isfinite(value) for value in result):
        raise ValidationError(f"{name} must contain only finite values.")
    return result


def validate_xy(xs: Sequence[float], ys: Sequence[float],
                minimum: int = 1) -> tuple[list[float], list[float]]:
    """Validate paired x/y data and return normalized float lists."""
    xs = validate_finite(xs, "X values")
    ys = validate_finite(ys, "Y values")
    if len(xs) != len(ys):
        raise ValidationError("X and Y values must have the same length.")
    if len(xs) < minimum:
        raise ValidationError(f"At least {minimum} data points are required.")
    return xs, ys
