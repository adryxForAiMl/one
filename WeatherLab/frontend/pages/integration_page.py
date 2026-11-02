"""Numerical integration workspace."""
from backend.integration import trapezoidal, simpson, simpson_three_eighths
from frontend.pages._base import MethodPage
from utils.helpers import compile_expression
from visualization.plots import sample_function


def build(parent):
    def calculate(v):
        f, a, b, n = compile_expression(v["f"]), float(v["a"]), float(v["b"]), int(v["n"])
        method = v["__select__"]
        rules = {"Trapezoidal": trapezoidal, "Simpson 1/3": simpson,
                 "Simpson 3/8": simpson_three_eighths}
        result = rules[method](f, a, b, n)
        xs, ys = sample_function(f, a, b)
        return f"Integral: {result:.10g}", f"{method} rule over [{a:g}, {b:g}] with {n} subintervals.", (xs, ys, "Integrand", [], True, "x", "f(x)")
    return MethodPage(parent, "Integration", "Approximate the area under a function over a chosen interval.",
        [("f", "Function f(x)", "sin(x)", "Example functions: sin(x), exp(-x**2), x**2."),
         ("__select__", "Rule", ["Simpson 1/3", "Trapezoidal", "Simpson 3/8"], ""),
         ("a", "Lower bound", "0", ""), ("b", "Upper bound", "3.14159", ""),
         ("n", "Intervals", "100", "Simpson 1/3 needs even n; Simpson 3/8 needs n divisible by 3.")], calculate,
        "The shaded chart area shows the signed integration region. Choose a subinterval count valid for the selected rule.")
