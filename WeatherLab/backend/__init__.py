"""Numerical algorithms available to the WeatherLab application."""

from .interpolation import (
    lagrange_interpolation, newton_divided_differences, newton_forward, newton_backward,
)
from .root_finding import bisection, newton_raphson, regula_falsi, secant
from .linear_systems import (
    gaussian_elimination, gauss_jordan, lu_decomposition, lu_solve, jacobi, gauss_seidel,
)
from .integration import simpson, simpson_three_eighths, trapezoidal
from .differentiation import derivative
from .differential_equations import solve_ivp
from .curve_fitting import polynomial_fit
from .spline import linear_spline, natural_cubic_spline
from .results import IterationResult

__all__ = ["lagrange_interpolation", "newton_divided_differences", "newton_forward", "newton_backward",
           "bisection", "newton_raphson", "regula_falsi", "secant", "gaussian_elimination",
           "gauss_jordan", "lu_decomposition", "lu_solve", "jacobi", "gauss_seidel", "simpson",
           "simpson_three_eighths", "trapezoidal", "derivative", "solve_ivp", "polynomial_fit",
           "linear_spline", "natural_cubic_spline", "IterationResult"]
