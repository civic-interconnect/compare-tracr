"""s04_charts_matplotlib.py - Matplotlib renderer.

make_matplotlib_compare(view) reads the fields and
labels from the view and returns a Matplotlib Figure.

Each geography is drawn as its own line.
"""

import matplotlib

matplotlib.use("Agg")  # safe default; the notebook/app decides how to display

import matplotlib.pyplot as plt

from s03_views import CompareView


def make_matplotlib_compare(view: CompareView) -> plt.Figure:
    """Render a multi-geography comparison as a Matplotlib line chart."""
    figure, axes = plt.subplots()

    for geography_name, group in view.data.group_by(
        view.series_field,
        maintain_order=True,
    ):
        xs = group[view.x_field].to_list()
        ys = group[view.y_field].to_list()

        label = (
            geography_name[0] if isinstance(geography_name, tuple) else geography_name
        )

        axes.plot(
            xs,
            ys,
            marker="o",
            label=label,
        )

    axes.set_title(view.title)
    axes.set_xlabel(view.x_label)
    axes.set_ylabel(view.y_label)
    axes.legend(title=view.series_label)

    figure.tight_layout()
    return figure
