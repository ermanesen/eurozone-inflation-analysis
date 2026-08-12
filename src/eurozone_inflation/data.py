"""Eurostat download, reshaping, and panel validation utilities."""

from __future__ import annotations

from collections.abc import Iterable
import json
import logging
from pathlib import Path

import pandas as pd
import requests

from .config import AnalysisConfig

LOGGER = logging.getLogger(__name__)
EUROSTAT_ENDPOINT = (
    "https://ec.europa.eu/eurostat/api/dissemination/"
    "statistics/1.0/data/{dataset}"
)


class DataDownloadError(RuntimeError):
    """Raised when Eurostat cannot return a usable response."""


class DataValidationError(ValueError):
    """Raised when the panel violates a required data-quality condition."""


def _position_codes(dimension: dict) -> dict[int, str]:
    index = dimension["category"]["index"]
    if isinstance(index, list):
        return dict(enumerate(index))
    return {position: code for code, position in index.items()}


def jsonstat_to_frame(payload: dict, value_name: str) -> pd.DataFrame:
    """Convert a Eurostat JSON-stat 2 response into a tidy DataFrame."""
    dimensions = payload["id"]
    sizes = payload["size"]
    code_maps = {
        name: _position_codes(payload["dimension"][name]) for name in dimensions
    }
    values = payload.get("value", {})
    value_items: Iterable[tuple[int, float]]
    if isinstance(values, list):
        value_items = ((i, value) for i, value in enumerate(values) if value is not None)
    else:
        value_items = ((int(i), value) for i, value in values.items())

    rows: list[dict] = []
    for flat_position, value in value_items:
        remainder = flat_position
        positions = [0] * len(sizes)
        for index in range(len(sizes) - 1, -1, -1):
            positions[index] = remainder % sizes[index]
            remainder //= sizes[index]
        row = {
            dimension: code_maps[dimension][position]
            for dimension, position in zip(dimensions, positions, strict=True)
        }
        row[value_name] = value
        rows.append(row)
    return pd.DataFrame(rows)


def _fetch_dataset(dataset: str, params: list[tuple[str, str]]) -> dict:
    url = EUROSTAT_ENDPOINT.format(dataset=dataset)
    try:
        response = requests.get(url, params=params, timeout=90)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, json.JSONDecodeError) as exc:
        raise DataDownloadError(f"Eurostat request failed for {dataset}: {exc}") from exc
    if payload.get("class") != "dataset":
        raise DataDownloadError(f"Eurostat returned no dataset for {dataset}.")
    return payload


def _time_and_geography_params(config: AnalysisConfig) -> list[tuple[str, str]]:
    params = [
        ("lang", "en"),
        ("freq", "M"),
        ("sinceTimePeriod", config.start),
        ("untilTimePeriod", config.end),
    ]
    params.extend(("geo", country) for country in config.countries)
    return params


def download_hicp(config: AnalysisConfig) -> pd.DataFrame:
    """Download HICP annual rates; no additional percentage change is applied."""
    params = _time_and_geography_params(config)
    params.extend((("unit", "RCH_A"), ("coicop", "CP00")))
    frame = jsonstat_to_frame(
        _fetch_dataset(config.hicp_dataset, params), "hicp_annual_rate"
    )
    return frame.rename(columns={"geo": "country", "time": "date"})[
        ["country", "date", "hicp_annual_rate"]
    ]


def download_unemployment(config: AnalysisConfig) -> pd.DataFrame:
    """Download the seasonally adjusted total unemployment rate."""
    params = _time_and_geography_params(config)
    params.extend(
        (
            ("unit", "PC_ACT"),
            ("s_adj", "SA"),
            ("age", "TOTAL"),
            ("sex", "T"),
        )
    )
    frame = jsonstat_to_frame(
        _fetch_dataset(config.unemployment_dataset, params), "unemployment_rate"
    )
    return frame.rename(columns={"geo": "country", "time": "date"})[
        ["country", "date", "unemployment_rate"]
    ]


def expected_grid(config: AnalysisConfig) -> pd.DataFrame:
    dates = pd.period_range(config.start, config.end, freq="M").astype(str)
    index = pd.MultiIndex.from_product(
        [config.countries, dates], names=["country", "date"]
    )
    return index.to_frame(index=False)


def validate_unique(frame: pd.DataFrame, label: str) -> None:
    duplicates = frame.duplicated(["country", "date"], keep=False)
    if duplicates.any():
        examples = frame.loc[duplicates, ["country", "date"]].head().to_dict("records")
        raise DataValidationError(
            f"{label} contains duplicate country-month rows; examples: {examples}"
        )


def build_panel(
    hicp: pd.DataFrame, unemployment: pd.DataFrame, config: AnalysisConfig
) -> tuple[pd.DataFrame, dict]:
    """Merge onto the expected grid so missing combinations remain observable."""
    validate_unique(hicp, "HICP")
    validate_unique(unemployment, "Unemployment")

    grid = expected_grid(config)
    panel = grid.merge(hicp, on=["country", "date"], how="left", validate="1:1")
    panel = panel.merge(
        unemployment, on=["country", "date"], how="left", validate="1:1"
    )
    missing_hicp = int(panel["hicp_annual_rate"].isna().sum())
    missing_unemployment = int(panel["unemployment_rate"].isna().sum())
    complete = int(panel.dropna(subset=["hicp_annual_rate", "unemployment_rate"]).shape[0])
    quality = {
        "countries": len(config.countries),
        "months": int(grid["date"].nunique()),
        "expected_rows": int(len(grid)),
        "complete_rows": complete,
        "missing_hicp": missing_hicp,
        "missing_unemployment": missing_unemployment,
        "duplicate_country_months": int(panel.duplicated(["country", "date"]).sum()),
        "start": config.start,
        "end": config.end,
    }
    if complete != len(grid):
        raise DataValidationError(
            "The configured panel is incomplete. Review reports/tables/quality_summary.json."
        )

    panel["date"] = pd.to_datetime(panel["date"])
    return panel.sort_values(["country", "date"]).reset_index(drop=True), quality


def load_snapshot(path: str | Path, config: AnalysisConfig) -> tuple[pd.DataFrame, dict]:
    """Load the committed, reproducible Eurostat snapshot."""
    frame = pd.read_csv(path, parse_dates=["date"])
    required = {"country", "date", "hicp_annual_rate", "unemployment_rate"}
    if set(frame.columns) != required:
        raise DataValidationError(f"Snapshot columns must be exactly {sorted(required)}.")
    validate_unique(frame.assign(date=frame["date"].dt.strftime("%Y-%m")), "Snapshot")
    expected = len(config.countries) * len(pd.period_range(config.start, config.end, freq="M"))
    quality = {
        "countries": int(frame["country"].nunique()),
        "months": int(frame["date"].nunique()),
        "expected_rows": expected,
        "complete_rows": int(frame.dropna().shape[0]),
        "missing_hicp": int(frame["hicp_annual_rate"].isna().sum()),
        "missing_unemployment": int(frame["unemployment_rate"].isna().sum()),
        "duplicate_country_months": int(frame.duplicated(["country", "date"]).sum()),
        "start": frame["date"].min().strftime("%Y-%m"),
        "end": frame["date"].max().strftime("%Y-%m"),
    }
    if quality["complete_rows"] != expected or quality["countries"] != len(config.countries):
        raise DataValidationError(f"Snapshot does not match the configured panel: {quality}")
    return frame.sort_values(["country", "date"]).reset_index(drop=True), quality


def refresh_snapshot(
    path: str | Path, config: AnalysisConfig
) -> tuple[pd.DataFrame, dict]:
    """Download, validate, and save an updated official Eurostat snapshot."""
    LOGGER.info("Downloading HICP annual rates from Eurostat.")
    hicp = download_hicp(config)
    LOGGER.info("Downloading seasonally adjusted unemployment rates from Eurostat.")
    unemployment = download_unemployment(config)
    panel, quality = build_panel(hicp, unemployment, config)
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(output, index=False, date_format="%Y-%m-%d")
    LOGGER.info("Saved %s validated country-month rows to %s.", len(panel), output)
    return panel, quality
