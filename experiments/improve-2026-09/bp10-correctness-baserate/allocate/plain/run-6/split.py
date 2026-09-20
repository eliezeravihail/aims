def split(n: int, k: int) -> list[int]:
    """
    Divide integer n into k parts as even as possible.
    Sum of returned parts equals n.
    Raises ValueError if k < 1.
    """
    if k < 1:
        raise ValueError("k must be at least 1")

    q, r = divmod(n, k)

    # Create k parts: first r parts have (q+1), rest have q
    return [q + 1] * r + [q] * (k - r)
