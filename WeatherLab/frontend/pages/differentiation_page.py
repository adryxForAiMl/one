"""Numerical differentiation workspace."""
from backend.differentiation import derivative
from frontend.pages._base import MethodPage
from utils.helpers import compile_expression
from visualization.plots import sample_function


def build(parent):
    def calculate(v):
        f, x = compile_expression(v["f"]), float(v["x"])
        order, step = int(v["order"]), float(v["h"])
        method = v["__select__"]
        method_key = {"Forward": "forward", "Backward": "backward",
                      "Central": "central", "Central (5-point)": "central-5"}[method]
        result = derivative(f, x, step, order, method_key)
        exact = v["exact"].strip()
        comparison = ""
        if exact:
            exact_value = compile_expression(exact)(x)
            comparison = f"  ·  analytical: {exact_value:.10g}  ·  error: {abs(result - exact_value):.3g}"
        lo, hi = x - 4 * step, x + 4 * step
        xs, ys = sample_function(f, lo, hi, 140)
        return f"f⁽{order}⁾({x:g}) ≈ {result:.10g}", f"{method} finite difference · h = {step:g}{comparison}", (xs, ys, "Function", [(x, f(x))], False, "x", "f(x)")
    return MethodPage(parent, "Differentiation", "Estimate the first or second derivative at a point.",
        [("f", "Function f(x)", "sin(x)", "Example: x**3 + 2*x."), ("x", "Evaluation point", "1", ""),
         ("h", "Step size", "0.001", "Smaller is not always more accurate due to rounding."),
         ("order", "Derivative order", "1", "Choose 1 or 2."),
         ("__select__", "Difference method", ["Central", "Forward", "Backward", "Central (5-point)"], ""),
         ("exact", "Analytical derivative at x (optional)", "", "Example for sin(x): cos(x).")], calculate,
        "Forward, backward, central, and five-point central formulas are supported for first and second derivatives.")
