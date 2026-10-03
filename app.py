"""Panel dashboard. Run with:  panel serve app.py --show"""
from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import panel as pn

from npi_verifier.client import NppesClient
from npi_verifier.frames import load_respondents, results_to_frame, summarize
from npi_verifier.render import render_empty, render_results
from npi_verifier.store import CachedRegistry, InternalRegistry
from npi_verifier.verifier import Verifier

SAMPLE_PATH = Path(__file__).parent / "data" / "sample_respondents.csv"
DB_PATH = Path(__file__).parent / "internal_registry.db"
INTERNAL, LIVE = "Internal registry", "Live NPPES registry"


def read_upload(content: bytes, filename: str | None) -> pd.DataFrame:
    """Read an uploaded .csv or .xlsx into a DataFrame of strings (NPIs must stay text)."""
    if filename and filename.lower().endswith(".xlsx"):
        return pd.read_excel(io.BytesIO(content), dtype=str)
    return pd.read_csv(io.BytesIO(content), dtype=str)


def build_app() -> pn.template.FastListTemplate:
    pn.extension()
    store = InternalRegistry(str(DB_PATH))

    source = pn.widgets.RadioButtonGroup(options=[INTERNAL, LIVE], value=LIVE, button_type="primary",
                                         button_style="outline")
    store_info = pn.pane.Markdown()
    upload = pn.widgets.FileInput(accept=".csv,.xlsx")
    run = pn.widgets.Button(name="Run verification", button_type="primary")
    verified_only = pn.widgets.Checkbox(name="Show verified only", value=False)
    message = pn.pane.Markdown("Upload a CSV or Excel (.xlsx) file with columns `npi`, `first_name`, "
                               "`last_name`, or leave it empty to use the sample file.")
    card = pn.pane.HTML(render_empty(), sizing_mode="stretch_width")
    state: dict = {}  # holds the last results so the checkbox can re-render without re-running

    def update_store_info():
        store_info.object = f"Saved in internal registry: **{store.count()}** doctors"

    def refresh(*_):
        if "df" in state:
            card.object = render_results(state["df"], state["summary"], verified_only.value)

    def on_run(_event=None):
        cache = None
        try:
            if upload.value:
                df_in = read_upload(upload.value, upload.filename)
            else:
                df_in = pd.read_csv(SAMPLE_PATH, dtype=str)
            respondents = load_respondents(df_in)
            if source.value == INTERNAL:
                registry = store
            else:
                cache = registry = CachedRegistry(store, NppesClient())
            results = Verifier(registry).verify_many(respondents)
        except Exception as exc:  # show any failure in the UI instead of a blank page
            message.object = f"**Could not run:** {exc}"
            return
        state["df"] = results_to_frame(results)
        state["summary"] = summarize(state["df"])
        s = state["summary"]
        text = f"Checked {s['total']} respondents. {s['duplicates']} rows share an NPI with another row."
        if cache:
            text += (f" {cache.internal_hits} found in the internal registry, "
                     f"{cache.live_hits} fetched live and saved.")
        elif store.count() == 0:
            text += " The internal registry is empty. Run once in Live mode to fill it."
        message.object = text
        update_store_info()
        refresh()

    run.on_click(on_run)
    verified_only.param.watch(refresh, "value")
    update_store_info()

    return pn.template.FastListTemplate(
        title="NPI Verification",
        theme_toggle=False,
        accent_base_color="#4f46e5",
        header_background="#4f46e5",
        sidebar=[pn.pane.Markdown("#### Registry"), source, store_info,
                 pn.pane.Markdown("#### Input file"), upload, run,
                 pn.Spacer(height=6), verified_only, message],
        main=[card],
    )


if __name__.startswith("bokeh"):
    build_app().servable()
