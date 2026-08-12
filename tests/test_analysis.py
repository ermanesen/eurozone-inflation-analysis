from pathlib import Path

import pytest

from eurozone_inflation.analysis import fit_models, prepare_model_data
from eurozone_inflation.config import load_config
from eurozone_inflation.data import load_snapshot


ROOT = Path(__file__).resolve().parents[1]
CONFIG = load_config(ROOT / "config" / "analysis.toml")


def test_lag_has_expected_cost_and_stays_within_country():
    panel, _ = load_snapshot(
        ROOT / "data" / "processed" / "eurozone_macro_panel.csv", CONFIG
    )
    model_data = prepare_model_data(panel, CONFIG.unemployment_lag_months)
    assert len(model_data) == 2_448
    first_de = model_data.loc[model_data["country"] == "DE"].iloc[0]
    assert first_de["date"].strftime("%Y-%m") == "2000-07"


def test_time_effects_attenuate_but_do_not_reverse_relationship():
    panel, _ = load_snapshot(
        ROOT / "data" / "processed" / "eurozone_macro_panel.csv", CONFIG
    )
    results, _ = fit_models(prepare_model_data(panel, CONFIG.unemployment_lag_months))
    country = results.loc[results["model"] == "Country fixed effects"].iloc[0]
    two_way = results.loc[
        results["model"] == "Country + month fixed effects"
    ].iloc[0]
    assert country["coefficient"] == pytest.approx(-0.259, abs=0.01)
    assert two_way["coefficient"] == pytest.approx(-0.106, abs=0.01)
    assert abs(two_way["coefficient"]) < abs(country["coefficient"])
