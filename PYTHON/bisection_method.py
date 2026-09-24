import math

def bisection(f, a, b, tol, max_iter):
    if f(a) * f(b) > 0:
        print("Error")
        return None

    for i in range(max_iter):
        c = (a + b) / 2

        print("Iteration:", i + 1)
        print("a =", a, "b =", b, "c =", c)

        if abs(f(c)) < tol:
            return c

        if f(a) * f(c) < 0:
            b = c
        else:
            a = c

    return c


expr = input("Enter f(x): ")
f = lambda x: eval(expr, {"x": x, "math": math})

a = float(input("Enter a: "))
b = float(input("Enter b: "))
tol = float(input("Enter tolerance: "))
max_iter = int(input("Enter max iterations: "))

root = bisection(f, a, b, tol, max_iter)

print("Approximate root:", root)