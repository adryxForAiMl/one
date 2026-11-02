"""Dense linear system solvers with validation and residual helpers."""
import math
from collections.abc import Sequence

import numpy as np

from .exceptions import ValidationError
from .results import IterationResult


def _validated_system(matrix: Sequence[Sequence[float]], vector: Sequence[float]):
    try:
        a = np.asarray(matrix, dtype=float)
        b = np.asarray(vector, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValidationError("Matrix and vector entries must be numeric.") from exc
    if a.ndim != 2 or a.shape[0] != a.shape[1] or b.ndim != 1 or len(b) != a.shape[0] or len(b) == 0:
        raise ValidationError("Matrix must be square and match the vector size.")
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValidationError("Matrix and vector values must be finite.")
    return a, b


def linear_residual(matrix: Sequence[Sequence[float]], vector: Sequence[float],
                    solution: Sequence[float]) -> float:
    """Return the Euclidean norm of Ax-b."""
    a, b = _validated_system(matrix, vector)
    x = np.asarray(solution, dtype=float)
    if x.shape != b.shape or not np.isfinite(x).all():
        raise ValidationError("Solution must be a finite vector matching the system size.")
    return float(np.linalg.norm(a @ x - b, ord=2))


def gaussian_elimination(matrix: Sequence[Sequence[float]], vector: Sequence[float]) -> list[float]:
    """Solve Ax=b by Gaussian elimination with partial pivoting."""
    a, b = _validated_system(matrix, vector)
    augmented = np.column_stack((a.copy(), b.copy()))
    n = len(b)
    scale = max(float(np.linalg.norm(a, ord=np.inf)), np.finfo(float).tiny)
    for col in range(n):
        pivot = col + int(np.argmax(np.abs(augmented[col:, col])))
        if abs(augmented[pivot, col]) <= 1e-14 * scale:
            raise ValidationError("System is singular or numerically ill-conditioned.")
        augmented[[col, pivot]] = augmented[[pivot, col]]
        for row in range(col + 1, n):
            factor = augmented[row, col] / augmented[col, col]
            augmented[row, col:] -= factor * augmented[col, col:]
    result = np.zeros(n)
    for row in range(n - 1, -1, -1):
        result[row] = (augmented[row, n] - augmented[row, row + 1:n] @ result[row + 1:n]) / augmented[row, row]
    return result.tolist()


def gauss_jordan(matrix: Sequence[Sequence[float]], vector: Sequence[float]) -> list[float]:
    """Solve Ax=b by Gauss–Jordan elimination with partial pivoting."""
    a, b = _validated_system(matrix, vector)
    augmented = np.column_stack((a.copy(), b.copy()))
    n = len(b)
    scale = max(float(np.linalg.norm(a, ord=np.inf)), np.finfo(float).tiny)
    for col in range(n):
        pivot = col + int(np.argmax(np.abs(augmented[col:, col])))
        if abs(augmented[pivot, col]) <= 1e-14 * scale:
            raise ValidationError("System is singular or numerically ill-conditioned.")
        augmented[[col, pivot]] = augmented[[pivot, col]]
        augmented[col] /= augmented[col, col]
        for row in range(n):
            if row != col:
                augmented[row] -= augmented[row, col] * augmented[col]
    return augmented[:, n].tolist()


def lu_decomposition(matrix: Sequence[Sequence[float]]) -> tuple[list[list[float]], list[list[float]], list[int]]:
    """Return L and U factors using Doolittle elimination with row pivoting.

    The result satisfies ``P @ A = L @ U``; the permutation vector records
    which original row occupies each row of the permuted system.
    """
    try:
        a = np.asarray(matrix, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValidationError("Matrix entries must be numeric.") from exc
    if a.ndim != 2 or a.shape[0] != a.shape[1] or not a.size or not np.isfinite(a).all():
        raise ValidationError("LU decomposition requires a finite, non-empty square matrix.")
    u, l = a.copy(), np.eye(a.shape[0])
    permutation = np.arange(a.shape[0])
    scale = max(float(np.linalg.norm(a, ord=np.inf)), np.finfo(float).tiny)
    for col in range(len(a)):
        pivot = col + int(np.argmax(np.abs(u[col:, col])))
        if abs(u[pivot, col]) <= 1e-14 * scale:
            raise ValidationError("Matrix is singular; LU factorization cannot continue.")
        if pivot != col:
            u[[col, pivot]] = u[[pivot, col]]
            permutation[[col, pivot]] = permutation[[pivot, col]]
            if col:
                l[[col, pivot], :col] = l[[pivot, col], :col]
        for row in range(col + 1, len(a)):
            l[row, col] = u[row, col] / u[col, col]
            u[row, col:] -= l[row, col] * u[col, col:]
    return l.tolist(), u.tolist(), permutation.tolist()


def lu_solve(matrix: Sequence[Sequence[float]], vector: Sequence[float]) -> list[float]:
    """Solve Ax=b using a pivoted LU factorization."""
    a, b = _validated_system(matrix, vector)
    lower, upper, permutation = lu_decomposition(a)
    l, u = np.asarray(lower), np.asarray(upper)
    rhs = b[permutation]
    n = len(b)
    y = np.zeros(n)
    for i in range(n):
        y[i] = rhs[i] - l[i, :i] @ y[:i]
    x = np.zeros(n)
    for i in range(n - 1, -1, -1):
        x[i] = (y[i] - u[i, i + 1:] @ x[i + 1:]) / u[i, i]
    return x.tolist()


def _iterative_solve(matrix, vector, tolerance: float, max_iterations: int, method: str) -> IterationResult[list[float]]:
    if not math.isfinite(tolerance) or tolerance <= 0 or max_iterations < 1:
        raise ValidationError("Tolerance and iteration limit must be positive and finite.")
    a, b = _validated_system(matrix, vector)
    if np.any(np.abs(np.diag(a)) <= 1e-14):
        raise ValidationError(f"{method} requires nonzero diagonal entries.")
    x = np.zeros(len(b))
    history = []
    for iteration in range(1, max_iterations + 1):
        previous = x.copy()
        for i in range(len(b)):
            if method == "jacobi":
                left = a[i, :i] @ previous[:i]
                right = a[i, i + 1:] @ previous[i + 1:]
            else:
                left = a[i, :i] @ x[:i]
                right = a[i, i + 1:] @ x[i + 1:]
            x[i] = (b[i] - left - right) / a[i, i]
        error = float(np.linalg.norm(x - previous, ord=np.inf))
        history.append(error)
        residual = float(np.linalg.norm(a @ x - b, ord=2))
        if error <= tolerance and residual <= tolerance * max(1.0, float(np.linalg.norm(b, ord=2))):
            return IterationResult(x.tolist(), iteration, residual, True, history)
    raise ValidationError(f"{method.title()} did not converge within {max_iterations} iterations.")


def jacobi(matrix: Sequence[Sequence[float]], vector: Sequence[float],
           tolerance: float = 1e-9, max_iterations: int = 500) -> IterationResult[list[float]]:
    """Solve Ax=b by Jacobi iteration; returns approximation and history."""
    return _iterative_solve(matrix, vector, tolerance, max_iterations, "jacobi")


def gauss_seidel(matrix: Sequence[Sequence[float]], vector: Sequence[float],
                 tolerance: float = 1e-9, max_iterations: int = 500) -> IterationResult[list[float]]:
    """Solve Ax=b by Gauss–Seidel iteration."""
    return _iterative_solve(matrix, vector, tolerance, max_iterations, "gauss-seidel")
