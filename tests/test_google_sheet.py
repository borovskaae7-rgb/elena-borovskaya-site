from vk_checker.google_sheet import _col


def test_col_conversion():
    assert _col(1) == "A"
    assert _col(26) == "Z"
    assert _col(27) == "AA"
    assert _col(52) == "AZ"
