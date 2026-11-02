"""Least squares polynomial curve fitting page."""
from backend.curve_fitting import polynomial_fit
from frontend.pages._base import MethodPage
from utils.helpers import parse_csv_numbers
from visualization.plots import sample_function


def build(parent):
    def calculate(v):
        xs, ys = parse_csv_numbers(v["x"]), parse_csv_numbers(v["y"])
        fit = polynomial_fit(xs, ys, int(v["degree"]))
        coeffs, model = fit.coefficients, fit.model
        curve_x, curve_y = sample_function(model, min(xs), max(xs))
        formula = " + ".join(f"{c:.5g}" if i == 0 else f"{c:+.5g}x^{i}" for i, c in enumerate(coeffs))
        return f"R² = {fit.r_squared:.6f}", f"y = {formula}\nDegree {len(coeffs) - 1} · {len(xs)} data points · SSE = {fit.residual_sum_squares:.5g}", (curve_x, curve_y, "Fitted model", list(zip(xs, ys)), False, "x", "y")
    return MethodPage(parent, "Curve Fitting", "Fit a least squares polynomial to noisy or observed data.",
        [("x", "X values", "0, 1, 2, 3, 4", "Comma-separated observations."),
         ("y", "Y values", "1, 2.2, 2.8, 4.2, 5", "Must have the same number of entries as X."),
         ("degree", "Polynomial degree", "1", "The point count must exceed the degree.")], calculate,
        "Coefficients minimize squared residuals. R² summarizes goodness of fit; avoid high polynomial degrees for small datasets.")
