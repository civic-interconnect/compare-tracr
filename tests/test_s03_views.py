"""Tests for s03_views.py."""

import polars as pl

from s02_analytics import CompareResult
from s03_views import CompareView, make_compare_view


def make_compare_result() -> CompareResult:
    """Return a small analytics result for view tests."""
    return CompareResult(
        data=pl.DataFrame(
            {
                "geography_id": [
                    "27001",
                    "27001",
                    "27003",
                    "27003",
                ],
                "geography_name": [
                    "Aitkin County, Minnesota",
                    "Aitkin County, Minnesota",
                    "Anoka County, Minnesota",
                    "Anoka County, Minnesota",
                ],
                "year": [
                    2023,
                    2024,
                    2023,
                    2024,
                ],
                "value": [
                    40.0,
                    42.5,
                    50.0,
                    55.0,
                ],
            }
        ),
        indicator_name="Employment rate",
        indicator_id="employment_rate",
        unit="percent",
    )


def test_make_compare_view_returns_compare_view() -> None:
    result = make_compare_result()

    view = make_compare_view(result)

    assert isinstance(view, CompareView)


def test_make_compare_view_preserves_data() -> None:
    result = make_compare_result()

    view = make_compare_view(result)

    assert view.data.equals(result.data)


def test_make_compare_view_sets_fields() -> None:
    result = make_compare_result()

    view = make_compare_view(result)

    assert view.x_field == "year"
    assert view.y_field == "value"
    assert view.series_field == "geography_name"


def test_make_compare_view_builds_title() -> None:
    result = make_compare_result()

    view = make_compare_view(result)

    assert view.title == "Employment rate"


def test_make_compare_view_builds_labels() -> None:
    result = make_compare_result()

    view = make_compare_view(result)

    assert view.x_label == "Year"
    assert view.y_label == "Percent"
    assert view.series_label == "Geography"


def test_make_compare_view_uses_value_when_unit_is_empty() -> None:
    result = CompareResult(
        data=pl.DataFrame(
            {
                "geography_id": ["27001"],
                "geography_name": ["Aitkin County, Minnesota"],
                "year": [2024],
                "value": [42.5],
            }
        ),
        indicator_name="Indicator A",
        indicator_id="indicator_a",
        unit="",
    )

    view = make_compare_view(result)

    assert view.y_label == "Value"


def test_make_compare_view_does_not_expose_indicator_id() -> None:
    result = make_compare_result()

    view = make_compare_view(result)

    assert not hasattr(view, "indicator_id")
