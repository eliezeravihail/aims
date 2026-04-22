"""A tiny module with a deliberately planted bug for pipeline demos.

Bug: ``add`` concatenates instead of summing when either operand is a string
that *looks* numeric. A user passing ``add("3", 4)`` expects 7 but gets "34".
"""


def add(a, b):
    return a + b


def multiply(a, b):
    return a * b
