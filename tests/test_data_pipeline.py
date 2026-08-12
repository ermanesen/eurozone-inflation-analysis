from pathlib import Path

import pandas as pd
import pytest

from eurozone_inflation.config import load_config
from eurozone_inflation.data import DataValidationError, load_snapshot, validate_unique


ROOT = Path(__file__).resolve().parents[1]
CONFIG = load_config(ROOT / "config" / "analysis.toml")
SNAPSHOT = ROOT / "data" / "processed" / "eurozone_macro_panel.csv"


def test_snapshot_is_complete_and_unique():
    panel, quality = load_snapshot(SNAPSHOT, CONFIG)
    assert len(panel) == 2_496
    assert quality["countries"] == 8
    assert quality["months"] == 312
    assert quality["duplicate_country_months"] == 0
    assert quality["missing_hicp"] == 0
    assert quality["missing_unemployment"] == 0


def test_hicp_is_the_published_annual_rate_not_a_second_transformation():
    panel, _ = load_snapshot(SNAPSHOT, CONFIG)
    observed = panel.loc[
        (panel["country"] == "NL")
        & (panel["date"] == pd.Timestamp("2022-10-01")),
        "hicp_annual_rate",
    ].item()
    assert observed == pytest.approx(16.8)


def test_duplicate_country_months_fail_loudly():
    duplicate = pd.DataFrame(
        {"country": ["DE", "DE"], "date": ["2024-01", "2024-01"]}
    )
    with pytest.raises(DataValidationError, match="duplicate country-month"):
        validate_unique(duplicate, "Synthetic")
