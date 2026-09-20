"""Reference for BP10 allocation sub-probe. Validates hidden tests only; not shown to arms.

Corner: the parts must sum EXACTLY to N. Naive floor (N//k each) drops the remainder
(sum < N). Correct: distribute the remainder of N mod k as +1 across that many parts."""

from typing import List


def split(n: int, k: int) -> List[int]:
    """Split integer n across k parts, as even as possible, summing exactly to n.
    The first (n mod k) parts are one larger. Requires k >= 1. Raises ValueError if k < 1.
    n may be negative; the same even-split-with-remainder rule applies via floor division."""
    if k < 1:
        raise ValueError("k must be >= 1")
    base = n // k
    rem = n - base * k  # 0 <= rem < k for k>0 (floor division)
    return [base + 1 if i < rem else base for i in range(k)]
