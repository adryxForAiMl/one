"""Pure Python Gauss-Jordan elimination for small traffic flow systems.

This module solves the linear estimation step only. Signal phase choices remain
the responsibility of the traffic signal controller.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class SolverResult:
    status: str
    solution: tuple[float, ...] | None
    rank: int
    residual: float | None = None
    row_operations: tuple[str, ...] = ()

    @property
    def is_unique(self) -> bool:
        return self.status == "unique"


def solve(A: Sequence[Sequence[float]], b: Sequence[float], tolerance: float = 1e-10) -> SolverResult:
    """Solve ``A x = b`` with partial pivoting and classify non-unique systems."""
    if not A or len(A) != len(b):
        raise ValueError("A must have at least one row and match the length of b")
    n = len(A[0])
    if n == 0 or any(len(row) != n for row in A):
        raise ValueError("A must be a non-empty rectangular matrix")
    if tolerance <= 0:
        raise ValueError("tolerance must be positive")

    augmented = [[float(v) for v in row] + [float(rhs)] for row, rhs in zip(A, b)]
    rows = len(augmented)
    pivot_columns: list[int] = []
    row_operations: list[str] = []
    pivot_row = 0

    for column in range(n):
        candidate = max(range(pivot_row, rows), key=lambda r: abs(augmented[r][column]), default=pivot_row)
        if pivot_row >= rows or abs(augmented[candidate][column]) <= tolerance:
            continue
        if candidate != pivot_row:
            augmented[pivot_row], augmented[candidate] = augmented[candidate], augmented[pivot_row]
            row_operations.append(f"R{pivot_row + 1} ↔ R{candidate + 1}")
        pivot = augmented[pivot_row][column]
        augmented[pivot_row] = [value / pivot for value in augmented[pivot_row]]
        if abs(pivot - 1.0) > tolerance:
            row_operations.append(f"R{pivot_row + 1} ← R{pivot_row + 1} / {pivot:.6g}")
        for row in range(rows):
            if row == pivot_row:
                continue
            factor = augmented[row][column]
            if abs(factor) > tolerance:
                row_operations.append(f"R{row + 1} ← R{row + 1} - ({factor:.6g}) × R{pivot_row + 1}")
                augmented[row] = [x - factor * y for x, y in zip(augmented[row], augmented[pivot_row])]
        pivot_columns.append(column)
        pivot_row += 1
        if pivot_row == rows:
            break

    for row in augmented:
        if all(abs(value) <= tolerance for value in row[:n]) and abs(row[n]) > tolerance:
            return SolverResult("inconsistent", None, len(pivot_columns), row_operations=tuple(row_operations))
    if len(pivot_columns) < n:
        status = "underdetermined" if rows < n else "singular"
        return SolverResult(status, None, len(pivot_columns), row_operations=tuple(row_operations))

    solution = [0.0] * n
    for row, column in enumerate(pivot_columns):
        solution[column] = augmented[row][n]
    residual = max(abs(sum(float(aij) * xj for aij, xj in zip(row, solution)) - float(rhs))
                   for row, rhs in zip(A, b))
    return SolverResult("unique", tuple(solution), len(pivot_columns), residual, tuple(row_operations))


def estimate_least_squares(A: Sequence[Sequence[float]], b: Sequence[float], tolerance: float = 1e-10) -> SolverResult:
    """Estimate a unique least-squares solution by solving normal equations."""
    if not A or len(A) != len(b):
        raise ValueError("A must have at least one row and match the length of b")
    n = len(A[0])
    if any(len(row) != n for row in A):
        raise ValueError("A must be rectangular")
    normal_A = [[sum(float(row[i]) * float(row[j]) for row in A) for j in range(n)] for i in range(n)]
    normal_b = [sum(float(row[i]) * float(rhs) for row, rhs in zip(A, b)) for i in range(n)]
    return solve(normal_A, normal_b, tolerance=tolerance)
