"""Test the tap's core functionality."""

from __future__ import annotations

from singer_sdk.testing import get_tap_test_class

from tap_npm.client import range_pairs
from tap_npm.tap import app


def test_range_pairs() -> None:
    """Test range_pairs() function."""
    assert list(range_pairs(100, 400, 50)) == [
        (100, 149),
        (150, 199),
        (200, 249),
        (250, 299),
        (300, 349),
        (350, 399),
    ]
    assert list(range_pairs(-100, 0, 16)) == [
        (-100, -85),
        (-84, -69),
        (-68, -53),
        (-52, -37),
        (-36, -21),
        (-20, -5),
        (-4, -1),
    ]
    assert list(range_pairs(0, 10, 2)) == [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]


TestTapNPM = get_tap_test_class(app.plugin)
