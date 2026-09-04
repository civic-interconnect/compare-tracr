"""app.py - NIST TraCR Community Comparison Notebook.

This notebook compares one community-resilience indicator over time across
multiple geographies using NIST Tracking Community Resilience (TraCR) data.

It is also a teaching template: re-point s00_nist_tracr_adapter.py at a
different dataset, and the rest of the pipeline and renderers keep working.

PLAN CELLS FIRST

1. Imports (always first, so the notebook is self-contained)
2. Opening title and introduction (Markdown)
3. Load and process the data
4. Controls: indicator, renderer, mode
5. Controls: geographies available for the selected indicator
6. Build the comparison result and renderer-facing view
7. Render: one chart, or all stacked for comparison
8. Closing (Markdown)

HOW MARIMO NOTEBOOKS WORK

Each cell is a FUNCTION.
The return value of one cell can be passed as an argument to another cell.
We never call the functions, so they don't need names other than `_` (underscore).
(You can give them names if you want, but the notebook engine ignores them.)

The notebook is REACTIVE: when a cell's code or inputs change,
the notebook engine reruns that cell and every cell that depends on it.

The notebook is always CONSISTENT with outputs reflecting current inputs.

The first cell imports all dependencies, so the notebook is SELF-CONTAINED.

All later cells include their dependencies in their argument list.
Some other cells return values that can be used in other cells.
A cell displays the value of its last expression.

A cell whose last line is an assignment or a bare return
(like data and view cells) displays nothing;
only markdown, control, and render cells are meant to show.

RULE: Each variable must be defined in exactly one cell.
Defining the same name in two cells is a marimo error.

INPUT WIDGETS/CONTROLS: A cell that builds an input widget
resets that widget to its default every time the cell reruns.
marimo reruns a cell whenever any argument in its signature changes.
So a widget-building cell must depend only on what genuinely determines its options.
"""

# === ONLY THIS AT THE TOP OF THE FILE ===

import marimo

__generated_with_marimo_version__ = "0.24.0"
app = marimo.App(width="medium")

# === FIRST CELL IMPORTS AND RETURNS DEPS TO MAKE IT SELF-CONTAINED ===


@app.cell
async def _():
    """Import every dependency and hand them to the rest of the notebook.

    This cell has no arguments: it is the root of the dependency graph.

    It returns each import so later cells can name them as parameters.
    The micropip block installs plotly and pyarrow only under WASM (emscripten),
    used when running in GitHub Pages or other browsers
    where they are not preinstalled.
    Running locally, they are available in the project Python environment.
    """
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


# ===  TYPICALLY START WITH A MARKDOWN TITLE AND OPENING ===


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
        - NOTE: Changing the indicator will reset the selected geographies.
          Improved behavior would require more advanced state management.
        """
    )


# ===  LOAD AND PROCESS THE DATA ===


@app.cell
def _(load_raw, mo, process):
    """Load the TraCR data and return the processed frame.

    Depends on the adapter (`load_raw`), the processor (`process`),
    and `mo` for `notebook_location()`, which resolves the three CSVs under public/
    both locally and in the exported WASM build for GitHub Pages.
    Reruns only when those change,
    so the expensive load does not repeat when the user touches a control.

    Returns `processed` for every downstream cell.
    """
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


# ===  CONTROLS: SELECT INDICATOR, RENDERER, AND MODE ===


@app.cell
def _(list_indicators, mo, processed):
    """Build the indicator, renderer, and mode controls.

    Depends on `processed` (to list indicators) and `mo`.
    It deliberately does NOT depend on `indicator`, `renderer`, or `mode` themselves.
    This cell creates them, so nothing the user toggles reruns it, and the three
    widgets never rebuild or reset once made.

    Keeping renderer and mode here (rather than in the geography cell below) is
    intentional: it keeps them out of that cell's argument list, so toggling
    them cannot rerun the geography cell and snap the selection back to its
    default.

    Returns the three control widgets.
    """
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


# ===  CONTROLS: SELECT GEOGRAPHY ===


@app.cell
def _(
    indicator,
    list_geographies_for_indicator,
    MAX_COMPARISON_GEOGRAPHIES,
    mo,
    processed,
):
    """Build the geography multiselect, scoped to the selected indicator.

    Depends ONLY on `indicator` (plus data helpers and the cap) on purpose.
    Different indicators cover different geographies, so the list must rebuild
    when the indicator changes.
    Rebuilding resets the selection to the default three.

    NOTE: This resets the selected geographies whenever the indicator changes.
    Preserving them across an indicator change might mean holding
    selections in `mo.state` and re-seeding the rebuilt widget from it.
    That is more state management than this template takes on and is left
    as a potential improvement.

    Do NOT add `renderer` or `mode` to this cell's arguments. This cell builds
    a widget, and a widget-building cell resets to its default every time it
    reruns; adding a control the user toggles would rerun this cell on every
    toggle and discard the user's chosen geographies.

    Returns the `geographies` widget.
    """
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


# ===  RETURN THE VIEW FOR RENDERING ===


@app.cell
def _(
    geographies,
    get_comparison,
    indicator,
    make_compare_view,
    MAX_COMPARISON_GEOGRAPHIES,
    processed,
):
    """Compute the comparison and build the renderer-facing view.

    Depends on the current `indicator` and `geographies` selections plus
    `processed`, so it recomputes whenever either changes.
     `get_comparison` raises if the indicator/geographies pair has no observations.

    Returns `view`.
    """
    # Clamp the selection before querying.
    # The multiselect default does not always survive WASM export:
    # on first paint the hydrated value can arrive
    # as the full option set, and max_selections
    # only limits new user picks,
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


# === DISPLAY THE RENDERED CHART(S) ===


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
    """Render `view` with one renderer, or all three stacked in Compare mode.

    Depends on `view` (the data), and on `mode`/`renderer` (the user's display
    choices).
    This cell is meant to rerun on those toggles:
    it consumes the controls, it does not create them, so
    rerunning re-renders without resetting anything.

    Altair is returned via `mo.as_html`, not `mo.ui.altair_chart`,
    because the interactive wrapper
    over-serializes under WASM (it will send a LOT of data)
    and can blow past marimo's output-size limit.

    Returns nothing; its last expression displays the chart.
    """

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


# ===  TYPICALLY END WITH A MARKDOWN SOURCE LINK AND CLOSING ===


@app.cell
def _(mo):
    """Render the closing suggestions and source link. Depends only on `mo`."""
    mo.md("""
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
        """)


if __name__ == "__main__":
    app.run()
