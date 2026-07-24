"""QuantForge-shaped as-of mid helper (intentionally buggy for AgentGrid dogfood)."""


def mid_as_of(series: list[float], i: int) -> float:
    """Return mid available at index i (no look-ahead)."""
    if i < 0 or i >= len(series):
        raise IndexError("index out of range")
    return series[-1]  # BUG: uses future bar
