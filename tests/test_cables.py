from powerplan.cables import select_cable_size, get_cable_ratings, CableConfiguration


def test_select_cable():
    assert select_cable_size(16, "4F1A", CableConfiguration.TWO_CORE) == 4
    assert select_cable_size(63, "4F1A", CableConfiguration.MULTI_CORE) == 16
    assert select_cable_size(400, "4F1A", CableConfiguration.TWO_SINGLE) == 240


def test_get_ratings():
    assert get_cable_ratings(16, "4F1A", CableConfiguration.MULTI_CORE) == {"rating": 63, "voltage_drop": 2.5}
