"""s04_charts_plotly.py - Plotly renderer.

make_plotly_compare(view) reads the fields and
labels from the view and returns a Plotly figure.

Each geography is drawn as its own line.
"""

import plotly.graph_objects as go

from s03_views import CompareView


def make_plotly_compare(view: CompareView) -> go.Figure:
    """Render a multi-geography comparison as a Plotly line chart."""
    figure = go.Figure()

    for geography_name, group in view.data.group_by(
        view.series_field,
        maintain_order=True,
    ):
        label = (
            geography_name[0] if isinstance(geography_name, tuple) else geography_name
        )

        figure.add_trace(
            go.Scatter(
                x=group[view.x_field].to_list(),
                y=group[view.y_field].to_list(),
                mode="lines+markers",
                name=label,
            )
        )

    figure.update_layout(
        title=view.title,
        xaxis_title=view.x_label,
        yaxis_title=view.y_label,
        legend_title=view.series_label,
    )

    return figure
