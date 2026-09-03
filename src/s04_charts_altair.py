"""s04_charts_altair.py - Altair renderer.

One function, one contract:
make_altair_compare(view) reads the fields and
labels from the view and returns an Altair chart.
"""

import altair as alt

from s03_views import CompareView


def make_altair_compare(view: CompareView) -> alt.Chart:
    """Render a multi-geography comparison as an Altair line chart."""
    return (
        alt.Chart(view.data)
        .mark_line(point=True)
        .encode(  # ty: ignore[unresolved-attribute]
            x=alt.X(
                f"{view.x_field}:O",
                title=view.x_label,
            ),
            y=alt.Y(
                f"{view.y_field}:Q",
                title=view.y_label,
            ),
            color=alt.Color(
                f"{view.series_field}:N",
                title=view.series_label,
            ),
            tooltip=[
                alt.Tooltip(
                    f"{view.series_field}:N",
                    title=view.series_label,
                ),
                alt.Tooltip(
                    f"{view.x_field}:O",
                    title=view.x_label,
                ),
                alt.Tooltip(
                    f"{view.y_field}:Q",
                    title=view.y_label,
                ),
            ],
        )
        .properties(title=view.title)
    )
