def split(n: int, k: int) -> list[int]:
    """Divide integer n into k parts as evenly as possible.

    The sum of returned parts equals n. Parts differ by at most 1.

    Args:
        n: Total amount to split
        k: Number of parts

    Returns:
        List of k integers summing to n, as balanced as possible

    Raises:
        ValueError: If k < 1
    """
    if k < 1:
        raise ValueError("k must be at least 1")

    base = n // k
    remainder = n % k

    result = [base] * k
    for i in range(remainder):
        result[i] += 1

    return result
