from ewma import ewma_update


def test_full_weight_on_observation():
    assert ewma_update(10.0, 20.0, alpha=1.0) == 20.0


def test_partial_blend():
    # alpha=0.5 → midpoint
    assert ewma_update(0.0, 10.0, alpha=0.5) == 5.0


def test_high_alpha_tracks_observation():
    # alpha=0.8 should land closer to observation than to prev
    out = ewma_update(0.0, 10.0, alpha=0.8)
    assert out == 8.0
