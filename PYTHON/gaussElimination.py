import numpy as np
def gauss_elimination(A, b):
    n = len(b)
    aug = np.hstack((A.astype(float), b.reshape(-1, 1)))

    # Forward Elimination
    for i in range(n):
        for j in range(i+1, n):
            factor = aug[j, i] / aug[i, i]
            aug[j] = aug[j] - factor * aug[i]
    # Back Substitution
    x = np.zeros(n)
    for i in range(n-1, -1, -1):
        x[i] = (aug[i, -1] - np.dot(aug[i, i+1:n], x[i+1:n])) / aug[i, i]
    return x
A = np.array([
    [2, 3, 1],
    [4, 1, -2],
    [3, 2, 3]
], dtype=float)
b = np.array([1, -2, 9], dtype=float)
solution = gauss_elimination(A, b)
print("Solution using Gauss Elimination Method:")
print(f"x = {solution[0]:.3f}")
print(f"y = {solution[1]:.3f}")
print(f"z = {solution[2]:.3f}")