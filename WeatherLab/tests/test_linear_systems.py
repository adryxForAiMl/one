import unittest
from backend.exceptions import ValidationError
from backend.linear_systems import (
    gaussian_elimination, gauss_jordan, lu_decomposition, lu_solve,
    jacobi, gauss_seidel, linear_residual,
)


class LinearSystemTests(unittest.TestCase):
    def test_gaussian_elimination(self):
        self.assertEqual(gaussian_elimination([[4, 1], [2, 3]], [9, 13]), [1.4, 3.4])

    def test_jacobi_converges(self):
        result, _ = jacobi([[4, 1], [2, 3]], [9, 13])
        self.assertAlmostEqual(result[0], 1.4, places=7)
        self.assertAlmostEqual(result[1], 3.4, places=7)

    def test_direct_solvers_and_pivoted_lu(self):
        matrix, vector = [[0, 2], [1, 3]], [4, 7]
        for solver in (gauss_jordan, lu_solve):
            answer = solver(matrix, vector)
            self.assertLess(linear_residual(matrix, vector, answer), 1e-12)
        lower, upper, permutation = lu_decomposition(matrix)
        self.assertEqual(permutation, [1, 0])
        permuted = [matrix[index] for index in permutation]
        for i in range(2):
            for j in range(2):
                self.assertAlmostEqual(sum(lower[i][k] * upper[k][j] for k in range(2)), permuted[i][j])

    def test_gauss_seidel_converges_and_singular_is_rejected(self):
        answer, _ = gauss_seidel([[4, 1], [2, 3]], [9, 13])
        self.assertAlmostEqual(answer[0], 1.4, places=7)
        with self.assertRaises(ValidationError):
            gaussian_elimination([[1, 2], [2, 4]], [3, 6])
