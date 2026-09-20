def split(n: int, k: int) -> list[int]:
    """Divide n into k balanced parts with remainder distributed evenly.

    Uses divmod to compute base size and remainder, then distributes
    the remainder across the first few parts to maintain balance.

    Args:
        n: Total amount to split
        k: Number of parts (must be >= 1)

    Returns:
        List of k integers that sum to n, ordered with larger parts first

    Raises:
        ValueError: If k is less than 1
    """
    if k < 1:
        raise ValueError("k must be at least 1")

    base, remainder = divmod(n, k)
    return [base + (1 if i < remainder else 0) for i in range(k)]
