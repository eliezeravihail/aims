def split(n: int, k: int) -> list[int]:
    """
    Divide integer n into k parts as even as possible.
    Sum of returned parts equals n.
    Raises ValueError if k < 1.
    """
    if k < 1:
        raise ValueError("k must be at least 1")

    base_amount = n // k
    remainder = n % k

    # Create k parts with base amount
    parts = [base_amount] * k

    # Distribute remainder across first 'remainder' parts
    for i in range(remainder):
        parts[i] += 1

    return parts
