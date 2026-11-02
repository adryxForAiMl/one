# Numerical methods

## Interpolation

Lagrange and Newton divided-difference polynomials support distinct X values.
Newton forward and backward formulas use finite-difference tables and require
equally spaced X values. Natural cubic splines use zero second derivatives at
the endpoints; piecewise linear splines connect adjacent knots. Spline
evaluation is restricted to the data interval.

## Root finding

Bisection and Regula Falsi require a bracketing interval with opposite signs.
Newton–Raphson requires a derivative expression; Secant uses two initial
guesses. Iterative results include residual, iteration count, and history.

## Linear systems

Gaussian elimination and Gauss–Jordan use partial pivoting. LU decomposition
uses row pivoting and returns factors and a permutation vector. Jacobi and
Gauss–Seidel report convergence history; singular systems and non-convergence
raise a validation error. Solutions are summarized with the Euclidean residual.

## Integration and differentiation

Composite trapezoidal integration accepts any positive interval count. Simpson
1/3 requires an even count; Simpson 3/8 requires a count divisible by three.
First and second derivatives support forward, backward, central, and five-point
central differences.

## Differential equations and fitting

The IVP solvers implement Euler, improved Euler (Heun), and classical RK4 for
`y' = f(x, y)`. Curve fitting uses NumPy least squares for linear or polynomial
models, reports coefficients, residual sum of squares, and R².
