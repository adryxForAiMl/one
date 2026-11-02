import pytest

from Traffic.backend.gauss_jordan import estimate_least_squares, solve


def test_known_system():
    result = solve([[2, 1], [1, -1]], [5, 1])
    assert result.status == "unique"
    assert result.solution == pytest.approx((2, 1))


def test_one_by_one():
    assert solve([[4]], [10]).solution == pytest.approx((2.5,))


def test_partial_pivoting():
    assert solve([[0, 1], [2, 3]], [1, 5]).solution == pytest.approx((1, 1))


def test_singular_and_underdetermined():
    assert solve([[1, 2], [2, 4]], [3, 6]).status == "singular"
    assert solve([[1, 2, 3], [2, 4, 6]], [3, 6]).status == "underdetermined"


def test_inconsistent():
    assert solve([[1, 2], [2, 4]], [3, 7]).status == "inconsistent"


def test_near_singular_respects_tolerance():
    assert solve([[1, 1], [1, 1 + 1e-12]], [2, 2 + 1e-12]).status == "singular"
    assert solve([[1, 1], [1, 1 + 1e-8]], [2, 2 + 1e-8], tolerance=1e-12).is_unique


def test_noisy_least_squares():
    result = estimate_least_squares([[1, 0], [0, 1], [1, 1]], [2, 3, 5.1])
    assert result.is_unique
    assert result.solution == pytest.approx((2.0333333333, 3.0333333333))
