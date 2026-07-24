"""ChainVenue-shaped basis helper (intentionally wrong sign for dogfood)."""


def basis_bps(clob_mid: float, amm_mid: float) -> int:
    """Positive when CLOB is rich vs AMM."""
    if clob_mid <= 0:
        raise ValueError("clob_mid must be positive")
    return int((amm_mid - clob_mid) / clob_mid * 10_000)
