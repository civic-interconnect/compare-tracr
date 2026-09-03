"""Tests for s02_analytics.py."""

import polars as pl
import pytest

from s02_analytics import (
    CompareResult,
    get_comparison,
    list_geographies,
    list_geographies_for_indicator,
    list_indicators,
)


def make_processed_data() -> pl.DataFrame:
    """Return a small processed dataset for analytics tests."""
    return pl.DataFrame(
        {
            "geography_id": [
                "27001",
                "27001",
                "27001",
                "27003",
                "27003",
                "27005",
            ],
            "geography_name": [
                "Aitkin County, Minnesota",
                "Aitkin County, Minnesota",
                "Aitkin County, Minnesota",
                "Anoka County, Minnesota",
                "Anoka County, Minnesota",
                "Becker County, Minnesota",
            ],
            "indicator_id": [
                "indicator_a",
                "indicator_a",
                "indicator_b",
                "indicator_a",
                "indicator_a",
                "indicator_b",
            ],
            "indicator_name": [
                "Indicator A",
                "Indicator A",
                "Indicator B",
                "Indicator A",
                "Indicator A",
                "Indicator B",
            ],
            "unit": [
                "percent",
                "percent",
                "count",
                "percent",
                "percent",
                "count",
            ],
            "year": [
                2024,
                2023,
                2024,
                2023,
                2024,
                2024,
            ],
            "value": [
                42.5,
                40.0,
                100.0,
                50.0,
                55.0,
                120.0,
            ],
        }
    )


def test_get_comparison_returns_compare_result() -> None:
    processed = make_processed_data()

    result = get_comparison(
        processed,
        geography_ids=["27001", "27003"],
        indicator_id="indicator_a",
    )

    assert isinstance(result, CompareResult)


def test_get_comparison_returns_requested_geographies_and_indicator_only() -> None:
    processed = make_processed_data()

    result = get_comparison(
        processed,
        geography_ids=["27001", "27003"],
        indicator_id="indicator_a",
    )

    assert result.data.rows() == [
        ("27001", "Aitkin County, Minnesota", 2023, 40.0),
        ("27001", "Aitkin County, Minnesota", 2024, 42.5),
        ("27003", "Anoka County, Minnesota", 2023, 50.0),
        ("27003", "Anoka County, Minnesota", 2024, 55.0),
    ]


def test_get_comparison_returns_expected_columns() -> None:
    processed = make_processed_data()

    result = get_comparison(
        processed,
        geography_ids=["27001", "27003"],
        indicator_id="indicator_a",
    )

    assert result.data.columns == [
        "geography_id",
        "geography_name",
        "year",
        "value",
    ]


def test_get_comparison_returns_metadata() -> None:
    processed = make_processed_data()

    result = get_comparison(
        processed,
        geography_ids=["27001", "27003"],
        indicator_id="indicator_a",
    )

    assert result.indicator_name == "Indicator A"
    assert result.indicator_id == "indicator_a"
    assert result.unit == "percent"


def test_get_comparison_raises_for_empty_geography_list() -> None:
    processed = make_processed_data()

    with pytest.raises(
        ValueError,
        match="At least one geography_id is required",
    ):
        get_comparison(
            processed,
            geography_ids=[],
            indicator_id="indicator_a",
        )


def test_get_comparison_raises_for_missing_series() -> None:
    processed = make_processed_data()

    with pytest.raises(
        ValueError,
        match="No observations",
    ):
        get_comparison(
            processed,
            geography_ids=["99999"],
            indicator_id="indicator_a",
        )


def test_list_geographies_returns_unique_pairs_sorted_by_name() -> None:
    processed = make_processed_data()

    result = list_geographies(processed)

    assert result == [
        ("27001", "Aitkin County, Minnesota"),
        ("27003", "Anoka County, Minnesota"),
        ("27005", "Becker County, Minnesota"),
    ]


def test_list_geographies_for_indicator_returns_only_available_geographies() -> None:
    processed = make_processed_data()

    result = list_geographies_for_indicator(
        processed,
        indicator_id="indicator_a",
    )

    assert result == [
        ("27001", "Aitkin County, Minnesota"),
        ("27003", "Anoka County, Minnesota"),
    ]


def test_list_geographies_for_indicator_returns_empty_list_when_none_exist() -> None:
    processed = make_processed_data()

    result = list_geographies_for_indicator(
        processed,
        indicator_id="missing_indicator",
    )

    assert result == []


def test_list_indicators_returns_unique_pairs_sorted_by_name() -> None:
    processed = make_processed_data()

    result = list_indicators(processed)

    assert result == [
        ("indicator_a", "Indicator A"),
        ("indicator_b", "Indicator B"),
    ]
