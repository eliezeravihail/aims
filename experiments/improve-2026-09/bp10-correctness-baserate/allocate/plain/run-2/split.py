def split(n: int, k: int) -> list[int]:
    """Distribute n items across k parts with maximum balance.

    Each part gets either floor(n/k) or ceil(n/k) items, ensuring
    the total is exactly n and parts are as equal as possible.

    Args:
        n: Total amount to distribute
        k: Number of recipient parts

    Returns:
        List of k positive integers summing to n

    Raises:
        ValueError: If k < 1
    """
    if k < 1:
        raise ValueError("k must be at least 1")

    parts = []
    for i in range(k):
        remaining_parts = k - i
        remaining_total = n - sum(parts)
        part_size = remaining_total // remaining_parts
        parts.append(part_size)

    return parts
