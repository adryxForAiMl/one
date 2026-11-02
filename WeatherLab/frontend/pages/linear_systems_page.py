"""Linear equation system solvers."""
from backend.linear_systems import (
    gaussian_elimination, gauss_jordan, lu_solve, jacobi, gauss_seidel, linear_residual,
)
from frontend.pages._base import MethodPage
from utils.helpers import parse_csv_numbers
from visualization.convergence import convergence_series


def build(parent):
    def calculate(v):
        rows = [parse_csv_numbers(row) for row in v["matrix"].split(";")]
        rhs = parse_csv_numbers(v["rhs"])
        method = v["__select__"]
        if method in ("Jacobi", "Gauss-Seidel"):
            solver = jacobi if method == "Jacobi" else gauss_seidel
            result = solver(rows, rhs, float(v["tol"]), int(v["iterations"]))
            answer, history = result
            px, py = convergence_series(history)
            plot = (px, py, "Iteration error", [], False, "Iteration", "∞-norm error")
            iterations = result.iteration_count
        else:
            solver = {"Gaussian elimination": gaussian_elimination,
                      "Gauss–Jordan": gauss_jordan, "LU decomposition": lu_solve}[method]
            answer = solver(rows, rhs)
            plot = None
            iterations = 0
        residual = linear_residual(rows, rhs, answer)
        headline = "Solution vector"
        table = "\n".join(f"x{i + 1} = {value:.10g}" for i, value in enumerate(answer))
        detail = f"{method}  ·  residual ‖Ax − b‖₂ = {residual:.3g}  ·  iterations: {iterations}"
        return headline, detail, plot, table
    return MethodPage(parent, "Linear Systems", "Solve Ax = b with direct or iterative numerical algorithms.",
        [("matrix", "Matrix A", "4, 1; 2, 3", "Rows separated by semicolons; values separated by commas."),
         ("rhs", "Vector b", "9, 13", "One value per matrix row."),
         ("__select__", "Solver", ["Gaussian elimination", "Gauss–Jordan", "LU decomposition", "Jacobi", "Gauss-Seidel"], ""),
         ("tol", "Tolerance", "1e-9", "Jacobi stopping threshold."),
         ("iterations", "Maximum iterations", "500", "Jacobi iteration cap.")], calculate,
        "Direct methods use partial pivoting. Iterative methods require convergence; the residual is reported for every solution.")
