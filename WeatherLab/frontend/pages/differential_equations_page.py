"""Initial value problem solver page."""
import math

from backend.differential_equations import solve_ivp
from backend.exceptions import ValidationError
from frontend.pages._base import MethodPage
from utils.helpers import compile_expression


def build(parent):
    def calculate(v):
        f = compile_expression(v["f"], variables=("x", "y"))
        solution = solve_ivp(f, float(v["x0"]), float(v["y0"]), float(v["end"]),
                             method=v["__select__"], step_size=float(v["h"]))
        xs, ys = solution
        exact_text = v["exact"].strip()
        exact = compile_expression(exact_text) if exact_text else None
        if exact:
            if not math.isclose(exact(xs[0]), ys[0], rel_tol=1e-5, abs_tol=1e-7):
                raise ValidationError("The supplied exact solution does not match the initial value.")
            for index in sorted(set((0, len(xs) // 2, len(xs) - 1))):
                x_value = xs[index]
                probe = 1e-5 * max(1.0, abs(x_value))
                exact_slope = (exact(x_value + probe) - exact(x_value - probe)) / (2 * probe)
                ode_slope = f(x_value, exact(x_value))
                if not math.isclose(exact_slope, ode_slope, rel_tol=2e-4, abs_tol=2e-5):
                    raise ValidationError("The supplied exact expression does not satisfy the ODE.")
        table_rows = ["       x              y numerical          y exact             error"]
        for x_value, y_value in zip(xs, ys):
            row = f"{x_value:12.6g}  {y_value:18.9g}"
            if exact:
                exact_value = exact(x_value)
                row += f"  {exact_value:18.9g}  {abs(y_value - exact_value):12.4g}"
            table_rows.append(row)
        detail = f"{v['__select__']} · {len(xs) - 1} steps · actual h={solution.step_size:.5g} · scroll the table for all values."
        return f"y({xs[-1]:g}) ≈ {ys[-1]:.10g}", detail, (xs, ys, "Numerical solution", [], False, "x", "y(x)"), "\n".join(table_rows)
    return MethodPage(parent, "Differential Equations", "Solve an initial value problem y′ = f(x, y) numerically.",
        [("f", "Slope f(x, y)", "x + y", "Use x and y; example y - x**2 + 1."),
         ("__select__", "Method", ["Runge-Kutta 4", "Heun", "Euler"], ""),
         ("x0", "Initial x", "0", ""), ("y0", "Initial y", "1", ""),
         ("end", "End x", "2", ""), ("h", "Step size", "0.05", "The interval is divided into equal steps to reach the end point."),
         ("exact", "Exact y(x) (optional)", "", "Example for y′=y, y(0)=1: exp(x).")], calculate,
        "Euler, Heun's improved Euler, and classical Runge–Kutta 4 methods are available. The solution table samples the full result.")
