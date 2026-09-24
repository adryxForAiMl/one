def lagrange(x, y, value):
    n = len(x)
    result = 0

    for i in range(n):
        term = y[i]

        for j in range(n):
            if i != j:
                term = term * (value - x[j]) / (x[i] - x[j])

        result = result + term

    return result


x = [1, 2, 4]
y = [2, 3, 5]

value = 3

result = lagrange(x, y, value)

print("f(3) =", result)