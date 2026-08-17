# from scipy.optimize import newton
# def f(x):
#  return x**2 - 4
# def df(x):
#  return 2*x
# root = newton(f, x0=1.5, fprime=df)
# print(f"Newton-Raphson Root: {root:.6f}")

def g(x):
 return (x + 2) ** (1/3)
x0 = 1.5
tolerance = 1e-6
max_iter = 100
for i in range(max_iter):
 x1 = g(x0)
 if abs(x1 - x0) < tolerance:
   print(f"Root by Iterative Method: {x1:.6f}")
   print(f"Converged in {i+1} iterations")
   break
 x0 = x1
else:
   print("Did not converge")