from src.listicle_pipeline.nodes.human_review import _parse_selection


def test_all_variants():
    assert _parse_selection("all", 5) == [0, 1, 2, 3, 4]
    assert _parse_selection("", 5) == [0, 1, 2, 3, 4]


def test_comma_list():
    assert _parse_selection("3,1,7", 8) == [2, 0, 6]


def test_range():
    assert _parse_selection("1-5", 8) == [0, 1, 2, 3, 4]


def test_mixed_range_and_list():
    assert _parse_selection("1-3,7", 8) == [0, 1, 2, 6]


def test_out_of_bounds_indices_dropped():
    assert _parse_selection("1,99,2", 3) == [0, 1]
