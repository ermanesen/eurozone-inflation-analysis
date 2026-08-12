"""Create the narrated analysis notebook from a small auditable template."""

from __future__ import annotations

import json
import logging
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "notebooks" / "eurozone_phillips_curve.ipynb"


def markdown(source: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in source.strip().splitlines()],
    }


def code(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in source.strip().splitlines()],
    }


cells = [
    markdown(
        """
# Eurozone inflation and unemployment

This notebook audits and estimates the relationship between Eurostat's **published annual HICP rate** and unemployment in eight euro-area economies from 2000 to 2025. The HICP series is already an annual rate of change, so it is never transformed with `pct_change(12)`.
"""
    ),
    code(
        """
from pathlib import Path
import json
import logging
import sys
import pandas as pd
from IPython.display import SVG, display

ROOT = Path.cwd().resolve()
if ROOT.name == "notebooks":
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

from eurozone_inflation.config import load_config
from eurozone_inflation.data import load_snapshot
from eurozone_inflation.analysis import descriptive_summary, fit_models, prepare_model_data
"""
    ),
    markdown(
        """
## 1. Load the validated panel

The committed snapshot makes the published result reproducible even when Eurostat revises live data. The loader asserts expected columns, complete coverage, and one row per country-month.
"""
    ),
    code(
        """
config = load_config(ROOT / "config" / "analysis.toml")
panel, quality = load_snapshot(
    ROOT / "data" / "processed" / "eurozone_macro_panel.csv", config
)
pd.Series(quality, name="value").to_frame()
"""
    ),
    markdown(
        """
## 2. Inspect the outcome

`hicp_annual_rate` is measured in percentage points and comes directly from `prc_hicp_manr` (`RCH_A`, `CP00`). The trend highlights the exceptional common inflation shock in 2021–2023.
"""
    ),
    code(
        """
monthly, descriptive = descriptive_summary(panel)
pd.Series(descriptive, name="value").to_frame()
"""
    ),
    code(
        """
display(SVG(filename=str(ROOT / "figures" / "inflation_trend.svg")))
"""
    ),
    markdown(
        """
## 3. Estimate two fixed-effects specifications

Unemployment is lagged six months within each country. Model 1 removes time-invariant country differences. Model 2 also absorbs common calendar-month shocks. Both use standard errors clustered by country.
"""
    ),
    code(
        """
model_data = prepare_model_data(panel, config.unemployment_lag_months)
results, fitted = fit_models(model_data)
results.round(4)
"""
    ),
    code(
        """
display(SVG(filename=str(ROOT / "figures" / "model_coefficients.svg")))
"""
    ),
    markdown(
        """
## 4. Interpretation

Month effects attenuate the unemployment coefficient, showing that common shocks explain a meaningful share of inflation variation. The corrected estimate remains negative; it does not reverse sign. The coefficient is an association, not a causal effect, and inference with eight country clusters should be treated cautiously.
"""
    ),
    code(
        """
display(SVG(filename=str(ROOT / "figures" / "phillips_partial_scatter.svg")))
"""
    ),
    markdown(
        """
## 5. Reproducibility

The complete pipeline is available in `src/eurozone_inflation/`. Run `python scripts/run_analysis.py` to rebuild all tables and figures from the snapshot, or add `--refresh` to request a new Eurostat snapshot with explicit filters. Automated tests verify the measurement definition, panel uniqueness, model sample, coefficients, notebook execution, and nonempty figures.
"""
    ),
]

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "version": "3.12"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(notebook, indent=1) + "\n", encoding="utf-8")
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logging.getLogger(__name__).info("Wrote %s", OUTPUT)
