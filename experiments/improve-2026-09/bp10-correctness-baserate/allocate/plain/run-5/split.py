def split(n: int, k: int) -> list[int]:
    """
    Divide integer n into k parts as even as possible.
    Sum of returned parts equals n.
    Raises ValueError if k < 1.
    """
    if k < 1:
        raise ValueError("k must be at least 1")

    quotient = n // k
    remainder = n % k

    # Build result by alternating: first 'remainder' parts get quotient+1,
    # remaining parts get quotient
    result = []
    for i in range(k):
        if i < remainder:
            result.append(quotient + 1)
        else:
            result.append(quotient)

    return result
