"""s02_analytics.py - Analytics layer.

Owns the CompareResult contract and its creation.
CompareResult is the boundary between analytics and visualization.
It contains the observations for one indicator
across multiple geographies, plus semantics needed to
understand those observations.

Rankings, percent differences, latest-value comparisons, min/max, and other
derived measures are additional analytics.
They get their own functions and small result types
when the application needs them.
They do NOT get added to CompareResult.

Hard rule: this module imports no charting or notebook library.
"""

from dataclasses import dataclass

import polars as pl

MAX_COMPARISON_GEOGRAPHIES = 8


@dataclass(frozen=True)
class CompareResult:
    """Observations and metadata for one indicator across geographies.

    data carries only what the comparison needs:

        geography_id
        geography_name
        year
        value

    The remaining fields carry the semantics needed to understand the values.
    """

    data: pl.DataFrame
    indicator_name: str  # human-readable NIST indicator name
    indicator_id: str  # stable source identifier
    unit: str  # "percent", "count", "index", ...


def get_comparison(
    processed: pl.DataFrame,
    geography_ids: list[str],
    indicator_id: str,
) -> CompareResult:
    """Ask for one indicator across multiple geographies.

    Filters the processed observations to the requested indicator and
    geographies, then packages the observations with their semantics.

    The caller is expected to pass a bounded set of geography_ids.
    This function does not cap the count; charts become unreadable and exceed
    Altair's 5,000-row limit past roughly a dozen series, so the UI limits
    the selection.
    """
    if not geography_ids:
        raise ValueError("At least one geography_id is required.")

    subset = processed.filter(
        (pl.col("indicator_id") == indicator_id)
        & pl.col("geography_id").is_in(geography_ids)
    ).sort(["geography_name", "year"])

    if subset.is_empty():
        raise ValueError(
            "No observations for "
            f"indicator_id={indicator_id!r}, "
            f"geography_ids={geography_ids!r}."
        )

    first = subset.row(0, named=True)

    data = subset.select(
        [
            "geography_id",
            "geography_name",
            "year",
            "value",
        ]
    )

    return CompareResult(
        data=data,
        indicator_name=first["indicator_name"],
        indicator_id=first["indicator_id"],
        unit=first["unit"],
    )


def list_geographies(processed: pl.DataFrame) -> list[tuple[str, str]]:
    """Return (geography_id, geography_name) pairs present in the data."""
    rows = (
        processed.select(["geography_id", "geography_name"])
        .unique()
        .sort("geography_name")
        .iter_rows()
    )
    return list(rows)


def list_geographies_for_indicator(
    processed: pl.DataFrame,
    indicator_id: str,
) -> list[tuple[str, str]]:
    """Return geographies having observations for one indicator."""
    rows = (
        processed.filter(pl.col("indicator_id") == indicator_id)
        .select(["geography_id", "geography_name"])
        .unique()
        .sort("geography_name")
        .iter_rows()
    )
    return list(rows)


def list_indicators(processed: pl.DataFrame) -> list[tuple[str, str]]:
    """Return (indicator_id, indicator_name) pairs present in the data."""
    rows = (
        processed.select(["indicator_id", "indicator_name"])
        .unique()
        .sort("indicator_name")
        .iter_rows()
    )
    return list(rows)
