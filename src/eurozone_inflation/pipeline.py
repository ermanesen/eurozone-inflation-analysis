"""End-to-end orchestration for published outputs."""

from __future__ import annotations

import json
from pathlib import Path

from .analysis import descriptive_summary, fit_models, prepare_model_data
from .config import load_config
from .data import load_snapshot, refresh_snapshot
from .visualize import (
    save_coefficient_figure,
    save_partial_scatter,
    save_trend_figure,
)


def run_pipeline(root: str | Path, refresh: bool = False) -> dict:
    project_root = Path(root).resolve()
    config = load_config(project_root / "config" / "analysis.toml")
    snapshot = project_root / "data" / "processed" / "eurozone_macro_panel.csv"
    tables = project_root / "reports" / "tables"
    figures = project_root / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)

    if refresh:
        panel, quality = refresh_snapshot(snapshot, config)
    else:
        panel, quality = load_snapshot(snapshot, config)

    model_data = prepare_model_data(panel, config.unemployment_lag_months)
    results, fitted = fit_models(model_data)
    monthly, descriptive = descriptive_summary(panel)
    quality["model_rows"] = int(len(model_data))
    quality["rows_removed_by_lag"] = int(len(panel) - len(model_data))

    results.to_csv(tables / "model_results.csv", index=False)
    monthly.to_csv(tables / "monthly_summary.csv", index=False, date_format="%Y-%m-%d")
    with (tables / "quality_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(quality, handle, indent=2)
        handle.write("\n")
    with (tables / "descriptive_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(descriptive, handle, indent=2)
        handle.write("\n")

    save_trend_figure(monthly, figures / "inflation_trend.svg")
    two_way_coefficient = float(
        results.loc[
            results["model"] == "Country + month fixed effects", "coefficient"
        ].iloc[0]
    )
    save_partial_scatter(
        model_data, two_way_coefficient, figures / "phillips_partial_scatter.svg"
    )
    save_coefficient_figure(results, figures / "model_coefficients.svg")

    return {
        "quality": quality,
        "descriptive": descriptive,
        "models": results.to_dict("records"),
        "fitted": fitted,
    }
