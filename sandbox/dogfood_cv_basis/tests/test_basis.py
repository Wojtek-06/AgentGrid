from basis import basis_bps


def test_positive_when_clob_rich():
    assert basis_bps(1.05, 1.00) > 0


def test_negative_when_clob_cheap():
    assert basis_bps(0.95, 1.00) < 0
