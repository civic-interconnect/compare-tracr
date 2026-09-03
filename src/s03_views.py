"""s03_views.py - View preparation layer.

Turns a CompareResult (analytics) into a CompareView (presentation).

CompareView is the contract every renderer consumes.
It holds what a comparison chart needs:

- the data
- which columns represent x, y, and series
- the human-facing title and axis labels

A renderer never sees an indicator_id.
"""

from dataclasses import dataclass

import polars as pl

from s02_analytics import CompareResult


@dataclass(frozen=True)
class CompareView:
    """Everything a comparison renderer needs, and nothing it does not."""

    data: pl.DataFrame
    x_field: str
    y_field: str
    series_field: str
    title: str
    x_label: str
    y_label: str
    series_label: str


def make_compare_view(result: CompareResult) -> CompareView:
    """Build the renderer-facing view from an analytics result."""
    return CompareView(
        data=result.data,
        x_field="year",
        y_field="value",
        series_field="geography_name",
        title=result.indicator_name,
        x_label="Year",
        y_label=result.unit.title() if result.unit else "Value",
        series_label="Geography",
    )
