"""Tests for the label to USDA search-query mapping."""

import pytest

from app.services.food_mapping import get_search_query


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("burger", "hamburger, plain"),
        ("pizza", "pizza, cheese, regular crust"),
        ("Fried Chicken", "chicken, fried"),
        ("  RICE  ", "rice, white, cooked"),
    ],
)
def test_mapped_labels_become_better_usda_queries(label, expected):
    assert get_search_query(label) == expected


def test_an_unmapped_label_is_searched_as_given_but_normalised():
    assert get_search_query("  Margherita Pizza ") == "margherita pizza"
