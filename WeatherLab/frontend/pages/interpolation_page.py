"""Lagrange interpolation workspace."""
from backend.interpolation import (
    lagrange_interpolation, newton_divided_differences, newton_forward, newton_backward,
)
from frontend.pages._base import MethodPage
from utils.helpers import parse_csv_numbers


def build(parent):
    def calculate(v):
        xs, ys, target = parse_csv_numbers(v["x"]), parse_csv_numbers(v["y"]), float(v["target"])
        method = v["__select__"]
        evaluators = {
            "Lagrange Interpolation": lagrange_interpolation,
            "Newton divided differences": newton_divided_differences,
            "Newton forward": newton_forward,
            "Newton backward": newton_backward,
        }
        evaluate = evaluators[method]
        estimate = evaluate(xs, ys, target)
        x_span = max(xs) - min(xs) or 1
        x_margin = max(1.0, .25 * x_span)
        low, high = min(min(xs), target) - x_margin, max(max(xs), target) + x_margin
        curve_x = [low + (high - low) * i / 199 for i in range(200)]
        curve_y = [evaluate(xs, ys, x) for x in curve_x]
        value_low, value_high = min(min(ys), estimate), max(max(ys), estimate)
        value_span = value_high - value_low or max(abs(value_low) * .1, 1.0)
        y_limits = (value_low - value_span, value_high + .75 * value_span)
        curve_title = "Lagrange polynomial" if method == "Lagrange Interpolation" else method
        return (f"{estimate:.3f} °C",
                f"Target X = {target:g}  ·  {len(xs)} data points  ·  {method}",
                (curve_x, curve_y, curve_title, list(zip(xs, ys)), False,
                 "Time (hours)", "Temperature (°C)", (target, estimate),
                 False, "INTERPOLATION CURVE", y_limits))
    page = MethodPage(parent, "Interpolation", "Estimate a value between observed data points with a polynomial model.",
        [("x", "Time (X values)", "9, 10, 11, 13", "Comma separated; each X must be unique."),
         ("y", "Temperature (Y values)", "24, 26, 29, 33", "One Y value for each X value."),
         ("target", "Target time (X)", "12", "The location to estimate."),
         ("__select__", "Method", ["Lagrange Interpolation", "Newton divided differences", "Newton forward", "Newton backward"], "Forward/backward require equally spaced X values.")], calculate,
        "Polynomial interpolation passes through all observed points. Forward and backward formulas require uniform spacing.",
        form_heading="DATA INPUT", result_heading="ESTIMATED TEMPERATURE",
        reset_label="Reset Data", show_form_intro=False, result_size=29,
        result_icon="thermometer", show_hints=False, show_method_note=False,
        result_unit="°C")
    page.run(calculate)
    return page
