import numpy as np
from scipy.interpolate import CubicHermiteSpline
x = np.array([0, 1, 2])
y = np.array([1, 2, 0])
dydx = np.array([1, -1, 1])
hermite_poly = CubicHermiteSpline(x, y, dydx)
x_val = 1.5
y_val = hermite_poly(x_val)
print(f"Value at x = {x_val}: {y_val:.4f}")