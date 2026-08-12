"""Configuration loading for the analysis pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


@dataclass(frozen=True)
class AnalysisConfig:
    countries: tuple[str, ...]
    country_names: dict[str, str]
    start: str
    end: str
    unemployment_lag_months: int
    hicp_dataset: str
    unemployment_dataset: str


def load_config(path: str | Path) -> AnalysisConfig:
    """Read and validate the TOML configuration."""
    config_path = Path(path)
    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)

    analysis = raw["analysis"]
    datasets = raw["datasets"]
    country_names = raw["country_names"]
    countries = tuple(analysis["countries"])

    if len(countries) != len(set(countries)):
        raise ValueError("Country codes must be unique.")
    if set(countries) != set(country_names):
        raise ValueError("Every configured country needs exactly one display name.")
    if analysis["start"] > analysis["end"]:
        raise ValueError("Analysis start must not be after its end.")

    return AnalysisConfig(
        countries=countries,
        country_names=dict(country_names),
        start=analysis["start"],
        end=analysis["end"],
        unemployment_lag_months=int(analysis["unemployment_lag_months"]),
        hicp_dataset=datasets["hicp"],
        unemployment_dataset=datasets["unemployment"],
    )
