"""Spline interpolation workspace."""
from backend.spline import linear_spline, natural_cubic_spline
from frontend.pages._base import MethodPage
from utils.helpers import parse_csv_numbers


def build(parent):
    def calculate(v):
        xs, ys, target = parse_csv_numbers(v["x"]), parse_csv_numbers(v["y"]), float(v["target"])
        method = v["__select__"]
        spline = linear_spline if method == "Linear" else natural_cubic_spline
        result = spline(xs, ys, target)
        curve_x = [xs[0] + (xs[-1] - xs[0]) * i / 199 for i in range(200)]
        curve_y = [spline(xs, ys, x) for x in curve_x]
        return f"S({target:g}) = {result:.10g}", f"{method} spline interpolation using {len(xs)} ordered knots.", (curve_x, curve_y, f"{method} spline", list(zip(xs, ys)), False, "x", "y", (target, result))
    return MethodPage(parent, "Spline Interpolation", "Interpolate smoothly or piecewise between ordered data knots.",
        [("x", "Ordered X knots", "0, 1, 2, 3", "Values must be strictly increasing."),
         ("y", "Y values", "0, 1, 1.5, 2", "One value for each knot."),
         ("__select__", "Spline type", ["Natural Cubic", "Linear"], ""),
         ("target", "Target X", "1.5", "Target must be within the knot range.")], calculate,
        "Natural cubic splines have zero endpoint curvature; linear splines connect adjacent knots with straight segments.")
