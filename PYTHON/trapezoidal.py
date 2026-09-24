def f(x):
    return x * x

a = 1
b = 3
n = 8

h = (b - a) / n

sum = (f(a) + f(b)) / 2

for i in range(1, n):
    x = a + i * h
    sum = sum + f(x)

result = h * sum

print("Approximate value of integral =", result)
