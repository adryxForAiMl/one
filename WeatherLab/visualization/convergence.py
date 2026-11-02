"""Plot data for iterative convergence histories."""


def convergence_series(history):
    values = [row[-1] if isinstance(row, (tuple, list)) else row for row in history]
    return list(range(1, len(values) + 1)), values
