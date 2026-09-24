import math

def f(x):
    return x * x

a = 1
b = 3

x1 = -1 / math.sqrt(3)
x2 = 1 / math.sqrt(3)

p1 = ((b - a) / 2) * x1 + (b + a) / 2
p2 = ((b - a) / 2) * x2 + (b + a) / 2

result = ((b - a) / 2) * (f(p1) + f(p2))

print("Approximate value =", result)
