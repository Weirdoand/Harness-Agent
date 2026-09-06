"""demo_pkg.utils 的单元测试。"""

import pytest

from demo_pkg.utils import add, is_even, multiply


class TestAdd:
    def test_positive_numbers(self):
        assert add(1, 2) == 3

    def test_negative_numbers(self):
        assert add(-1, -2) == -3

    def test_mixed_sign(self):
        assert add(5, -3) == 2

    def test_floats(self):
        assert add(1.5, 2.5) == 4.0


class TestMultiply:
    def test_positive_numbers(self):
        assert multiply(3, 4) == 12

    def test_zero(self):
        assert multiply(5, 0) == 0

    def test_negative(self):
        assert multiply(-2, 6) == -12

    def test_floats(self):
        assert multiply(1.5, 2.0) == 3.0


class TestIsEven:
    @pytest.mark.parametrize("n", [0, 2, 4, -4, 100])
    def test_even_numbers(self, n):
        assert is_even(n) is True

    @pytest.mark.parametrize("n", [1, 3, -5, 101])
    def test_odd_numbers(self, n):
        assert is_even(n) is False
