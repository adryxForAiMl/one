"""Least-squares linear and polynomial curve fitting."""
from dataclasses import dataclass
from collections.abc import Sequence
from typing import Callable

import numpy as np

from .exceptions import ValidationError
from .validators import validate_xy


@dataclass
class FitResult:
    coefficients: list[float]
    r_squared: float
    residual_sum_squares: float
    model: Callable[[float], float]

    def __iter__(self):
        """Preserve ``coefficients, model = polynomial_fit(...)`` compatibility."""
        yield self.coefficients
        yield self.model


def polynomial_fit(xs: Sequence[float], ys: Sequence[float], degree: int = 1) -> FitResult:
    """Fit a polynomial by least squares and return coefficients and R².

    Coefficients use ascending powers: c[0] + c[1]x + c[2]x² + ...
    """
    xs, ys = validate_xy(xs, ys, minimum=2)
    if not isinstance(degree, int) or degree < 0 or len(xs) <= degree:
        raise ValidationError("Polynomial degree must be nonnegative and lower than the point count.")
    x_array, y_array = np.asarray(xs), np.asarray(ys)
    design = np.vander(x_array, N=degree + 1, increasing=True)
    coefficients, _, rank, _ = np.linalg.lstsq(design, y_array, rcond=None)
    if rank < degree + 1:
        raise ValidationError("The data does not contain enough distinct X values for this degree.")
    predicted = design @ coefficients
    residual_sum_squares = float(np.sum((y_array - predicted) ** 2))
    total_sum_squares = float(np.sum((y_array - np.mean(y_array)) ** 2))
    r_squared = 1.0 if total_sum_squares == 0 and residual_sum_squares == 0 else (
        0.0 if total_sum_squares == 0 else 1.0 - residual_sum_squares / total_sum_squares
    )
    coeffs = coefficients.tolist()
    model = lambda x: float(np.polynomial.polynomial.polyval(x, coefficients))
    return FitResult(coeffs, r_squared, residual_sum_squares, model)
