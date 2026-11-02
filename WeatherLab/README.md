# WeatherLab — Numerical Methods Studio

WeatherLab is a Python desktop app for exploring numerical methods with an
interactive dark interface and embedded Matplotlib charts.

## Features

- Lagrange, Newton divided-difference, Newton forward, and Newton backward interpolation
- Bisection, Regula Falsi, Newton–Raphson, and Secant root finding
- Gaussian elimination, Gauss–Jordan, pivoted LU, Jacobi, and Gauss–Seidel linear solvers
- Composite trapezoidal, Simpson 1/3, and Simpson 3/8 integration
- Euler, Heun, and fourth-order Runge–Kutta ODE solvers
- Linear and configurable polynomial least-squares fitting with R²
- Natural cubic and piecewise linear spline interpolation
- Forward, backward, central, and five-point numerical differentiation (open from Learning Roadmap)
- Safe math expression parsing, input validation, residual/error summaries, and plots
- Orange-on-black interface, responsive method pages, and a lightweight meteor animation

The compact sidebar follows the reference layout. Numerical Differentiation is
available as an additional workspace from the Learning Roadmap page.

## Architecture

- `backend/`: numerical algorithms, validation, domain errors, and structured results
- `frontend/`: CustomTkinter window, theme, navigation, components, and method pages
- `visualization/`: reusable plot-data and convergence helpers
- `utils/`: safe expression parsing, CSV input parsing, constants, and logging
- `tests/`: numerical regression and edge-case tests
- `docs/`: project and numerical-method notes

Backend methods accept Python values and do not depend on Tkinter. NumPy is used
for dense linear algebra and least-squares fitting.

## Requirements

- macOS with Python 3.14 (also suitable for recent Python 3 versions supported by the dependencies)
- CustomTkinter, Matplotlib, NumPy, and Pytest

## Setup and launch on macOS (zsh)

From this folder (`WeatherLab/`):

```zsh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 app.py
```

If `.venv` already exists, activate it and run `python3 -m pip install -r requirements.txt` before launching.

## Tests

With the environment activated, from `WeatherLab/`:

```zsh
python3 -m pytest -q
```

## Supported expressions and limitations

Function inputs support arithmetic (`+`, `-`, `*`, `/`, powers), parentheses,
`pi`, `e`, and the `sin`, `cos`, `tan`, `exp`, `log`, `log10`, and `sqrt`
functions. Expressions are parsed through an allowlist; Python code is not
executed. Root bracketing methods require a sign change, iterative linear
solvers may not converge for every matrix, and spline interpolation rejects
extrapolation. Exact derivatives and ODE solutions are optional user-provided
expressions; the app does not infer symbolic formulas.

The sample interpolation values are an educational estimate, not a verified
weather forecast.
