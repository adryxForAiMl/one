"""Root finding methods."""
from backend.root_finding import bisection, regula_falsi, newton_raphson, secant
from frontend.pages._base import MethodPage
from utils.helpers import compile_expression
from visualization.plots import sample_function


def build(parent):
    def calculate(v):
        f = compile_expression(v["f"])
        method = v["__select__"]
        if method == "Newton-Raphson":
            df = compile_expression(v["df"])
            result = newton_raphson(f, df, float(v["a"]), float(v["tol"]), int(v["iterations"]))
        elif method == "Secant":
            result = secant(f, float(v["a"]), float(v["b"]), float(v["tol"]), int(v["iterations"]))
        else:
            solver = bisection if method == "Bisection" else regula_falsi
            result = solver(f, float(v["a"]), float(v["b"]), float(v["tol"]), int(v["iterations"]))
        root, history = result
        low, high = sorted((float(v["a"]), float(v["b"])))
        margin = (high - low) * .08 or 1.0
        function_x, function_y = sample_function(f, low - margin, high + margin)
        convergence_x = [max(1, row[0]) for row in history]
        convergence_y = [max(abs(row[2]), 1e-16) for row in history]
        charts = [
            (function_x, function_y, "f(x)", [(root, f(root))], False, "x", "f(x)"),
            (convergence_x, convergence_y, "Absolute residual", [], False, "Iteration", "|f(x)|", None, True),
        ]
        return f"Root: {root:.10g}", f"Iterations: {result.iteration_count}  ·  Residual: {result.residual:.3g}  ·  {method}", {"charts": charts}
    return MethodPage(parent, "Root Finding", "Find where a function crosses zero and inspect convergence.",
        [("f", "Function f(x)", "x^3 - x - 2", "Use x, arithmetic, powers, sin, cos, exp, log or sqrt."),
         ("__select__", "Algorithm", ["Bisection", "Regula Falsi", "Newton-Raphson", "Secant"], ""),
         ("a", "Start / left endpoint", "1", "Newton uses this as its initial guess."),
         ("b", "Right endpoint", "2", "Used by bracketing methods."),
         ("df", "Derivative f'(x)", "3*x^2 - 1", "Used by Newton-Raphson."),
         ("tol", "Tolerance", "1e-8", "Stop threshold."),
         ("iterations", "Maximum iterations", "100", "")], calculate,
        "Bisection and Regula Falsi need endpoints with opposite signs. Newton needs f′(x); Secant needs two guesses.")
