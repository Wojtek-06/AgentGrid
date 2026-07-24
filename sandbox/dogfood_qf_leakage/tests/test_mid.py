from research_mid import mid_as_of


def test_as_of_does_not_use_future():
    series = [100.0, 101.0, 102.0]
    assert mid_as_of(series, 0) == 100.0
    assert mid_as_of(series, 1) == 101.0
