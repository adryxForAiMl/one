# import turtle

# t = turtle.Turtle()

# t.forward(100)

# turtle.done()


import numpy as np
from scipy.interpolate import lagrange
x_points = np.array([1, 2, 3])
y_points = np.array([2, 3, 5])
poly = lagrange(x_points, y_points)
print("Lagrange Polynomial:")
print(poly)
x_val = 2.5
y_val = poly(x_val)
print(f"Value at x = {x_val}: {y_val:.4f}")