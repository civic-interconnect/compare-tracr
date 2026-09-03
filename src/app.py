"""app.py - NIST TraCR Community Comparison Notebook.

This notebook compares one community-resilience indicator over time across
multiple geographies using NIST Tracking Community Resilience (TraCR) data.

It is also a teaching template: re-point s00_nist_tracr_adapter.py at a
different dataset, and the rest of the pipeline and renderers keep working.

PLAN CELLS
1. Imports
2. Opening title and introduction (Markdown)
3. Load and process the data
4. Controls: indicator, renderer, mode
5. Controls: geographies available for the selected indicator
6. Build the comparison result and renderer-facing view
7. Render: one chart, or all stacked for comparison
8. Closing (Markdown)
"""

import marimo

__generated_with_marimo_version__ = "0.24.0"
app = marimo.App(width="medium")


@app.cell
async def _():
    import sys

    import altair as alt

    # Altair hands chart data to a "data transformer" before rendering. The
    # environment's default (esp. under marimo/WASM) can serialize even a small
    # frame into tens of MB. "default" with a raised row cap inlines the rows
    # as plain JSON, which stays small for the handful of series we chart.
    alt.data_transformers.enable("default", max_rows=10000)

    import marimo as mo
    import matplotlib.pyplot as plt
    import polars as pl

    if sys.platform == "emscripten":
        import micropip

        await micropip.install(["plotly", "pyarrow"])

    import plotly.express as px

    from s00_nist_tracr_adapter import load_raw
    from s01_process_data import process
    from s02_analytics import (
        MAX_COMPARISON_GEOGRAPHIES,
        get_comparison,
        list_geographies_for_indicator,
        list_indicators,
    )
    from s03_views import make_compare_view
    from s04_charts_altair import make_altair_compare
    from s04_charts_matplotlib import make_matplotlib_compare
    from s04_charts_plotly import make_plotly_compare

    return (
        get_comparison,
        list_geographies_for_indicator,
        list_indicators,
        load_raw,
        make_altair_compare,
        make_compare_view,
        make_matplotlib_compare,
        make_plotly_compare,
        MAX_COMPARISON_GEOGRAPHIES,
        mo,
        process,
    )


@app.cell
def _(mo):
    mo.md(
        """
        # NIST TraCR Community Comparison

        Pick one community-resilience indicator and compare how it changes
        over time across multiple geographies.

        - Choose an **indicator** first.
        - Select up to eight **geographies** that have observations for that
          indicator.
        - Choose one **renderer**, or switch to **Compare all** to see the same
          view rendered differently.
        """
    )


@app.cell
def _(load_raw, mo, process):
    tracr_path = mo.notebook_location() / "public" / "TraCR_v1_database.csv"

    metadata_path = (
        mo.notebook_location() / "public" / "TraCR_Metadata_Column_Metadata.csv"
    )

    geography_path = mo.notebook_location() / "public" / "all-geocodes-v2020.csv"

    processed = process(
        load_raw(
            tracr_path,
            metadata_path=metadata_path,
            geography_path=geography_path,
        )
    )

    return (processed,)


@app.cell
def _(list_indicators, mo, processed):
    indicators = list_indicators(processed)

    indicator = mo.ui.dropdown(
        options={name: indicator_id for indicator_id, name in indicators},
        value=indicators[0][1],
        label="Indicator",
    )

    renderer = mo.ui.dropdown(
        options=[
            "Altair",
            "Plotly",
            "Matplotlib",
        ],
        value="Altair",
        label="Renderer",
    )

    mode = mo.ui.radio(
        options=[
            "Single",
            "Compare all",
        ],
        value="Single",
        label="Mode",
    )

    mo.vstack(
        [
            indicator,
            mo.hstack([renderer, mode], gap=1, justify="start"),
        ],
        gap=1,
    )

    return indicator, mode, renderer


@app.cell
def _(
    indicator,
    list_geographies_for_indicator,
    MAX_COMPARISON_GEOGRAPHIES,
    mo,
    processed,
    renderer,
):

    available_geographies = list_geographies_for_indicator(
        processed,
        indicator_id=indicator.value,
    )

    geography_options = {
        name: geography_id for geography_id, name in available_geographies
    }

    # Start with a small, valid selection so the first render is meaningful
    # and never accidentally the whole country.
    default_geographies = [name for _, name in available_geographies[:3]]

    geographies = mo.ui.multiselect(
        options=geography_options,
        value=default_geographies,
        max_selections=MAX_COMPARISON_GEOGRAPHIES,  # frontend refuses a 4,000-series chart
        # enforce the cap in the backend as well
        label=f"Geographies (up to {MAX_COMPARISON_GEOGRAPHIES})",
    )

    # display
    geographies

    # return for use elsewhere
    return (geographies,)


@app.cell
def _(
    geographies,
    get_comparison,
    indicator,
    make_compare_view,
    MAX_COMPARISON_GEOGRAPHIES,
    processed,
):
    # Clamp the selection before querying.
    # The multiselect default does not  always survive WASM export:
    # on first paint the hydrated value can arrive
    # as the full option set, and max selections
    # only limits *new* user picks,
    # not an oversized initial value.
    # Bounding here guarantees the renderer never receives
    # more series than the chart can hold, online or local.
    selected_ids = list(geographies.value)[:MAX_COMPARISON_GEOGRAPHIES]

    result = get_comparison(
        processed,
        geography_ids=selected_ids,
        indicator_id=indicator.value,
    )

    view = make_compare_view(result)

    return (view,)


@app.cell
def _(
    geographies,
    make_altair_compare,
    make_matplotlib_compare,
    make_plotly_compare,
    mo,
    mode,
    renderer,
    view,
):
    def render_one(name):
        if name == "Altair":
            chart = make_altair_compare(view)
            # DO NOT USE: mo.ui.altair_chart(chart).
            # That appears to serialize the whole set of series
            # making it way too big.
            # We lose click interactivity in this context.
            return mo.as_html(chart)
        if name == "Plotly":
            chart = make_plotly_compare(view)
            return mo.ui.plotly(chart)
        if name == "Matplotlib":
            chart = make_matplotlib_compare(view)
            return mo.as_html(chart)

        raise ValueError(f"Unknown renderer: {name}")

    if not geographies.value:
        output = mo.md("*Select at least one geography to compare.*")
    elif mode.value == "Compare all":
        output = mo.vstack(
            [
                render_one(name)
                for name in [
                    "Altair",
                    "Plotly",
                    "Matplotlib",
                ]
            ],
            gap=2,
        )
    else:
        output = render_one(renderer.value)

    output
    return


@app.cell
def _(mo):
    mo.md(
        """
        ## Suggestions

        - **Improve `s01`.** Processing is deliberately minimal.
          Add handling for suppressed values, revised indicators, or missing years.
          Document decisions.
        - **Add an analytic.** Latest-value ranking, percent difference,
          convergence, or divergence can be separate functions in `s02`
          returning their own small result types.
        - **Change the comparison.** Compare different communities, states,
          or other available geographies.

        [Source](https://github.com/civic-interconnect/compare-tracr)
        """
    )


if __name__ == "__main__":
    app.run()
