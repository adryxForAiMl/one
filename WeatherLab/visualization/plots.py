"""Numerical method plot data builders."""

import math


def sample_function(function, low, high, count=240):
    if count < 2:
        raise ValueError("At least two plot samples are required.")
    xs = [low + (high - low) * i / (count - 1) for i in range(count)]
    ys = []
    for x in xs:
        try:
            value = function(x)
            ys.append(value if math.isfinite(value) else math.nan)
        except (ValueError, OverflowError, ZeroDivisionError):
            ys.append(math.nan)
    return xs, ys


def points_series(xs, ys):
    return list(xs), list(ys)
