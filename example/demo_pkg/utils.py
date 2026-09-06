"""demo_pkg.utils - 提供一些简单的数学工具函数。"""

from __future__ import annotations


def add(a: int | float, b: int | float) -> int | float:
    """返回两个数的和。"""
    return a + b


def multiply(a: int | float, b: int | float) -> int | float:
    """返回两个数的乘积。"""
    return a * b


def is_even(n: int) -> bool:
    """判断一个整数是否为偶数。"""
    return n % 2 == 0
