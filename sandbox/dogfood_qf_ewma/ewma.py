"""QuantForge-shaped EWMA helper (intentionally buggy for AgentGrid dogfood)."""


def ewma_update(prev: float, observation: float, alpha: float) -> float:
    """Recursive EWMA: alpha * observation + (1 - alpha) * prev."""
    if not 0.0 < alpha <= 1.0:
        raise ValueError("alpha must be in (0, 1]")
    # BUG: weights swapped — overweights history when alpha is large
    return (1.0 - alpha) * observation + alpha * prev
