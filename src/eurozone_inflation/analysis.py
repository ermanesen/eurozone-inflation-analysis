"""Feature engineering and panel estimators."""

from __future__ import annotations

import pandas as pd
from linearmodels.panel import PanelOLS
from scipy.stats import t as student_t


def prepare_model_data(panel: pd.DataFrame, lag_months: int = 6) -> pd.DataFrame:
    """Create an exact within-country unemployment lag on a validated monthly panel."""
    frame = panel.sort_values(["country", "date"]).copy()
    frame["unemployment_lag6"] = frame.groupby("country", sort=False)[
        "unemployment_rate"
    ].shift(lag_months)
    return frame.dropna(subset=["hicp_annual_rate", "unemployment_lag6"]).reset_index(
        drop=True
    )


def _tidy_result(result, model_name: str) -> dict:
    parameter = "unemployment_lag6"
    coefficient = float(result.params[parameter])
    std_error = float(result.std_errors[parameter])
    t_stat = coefficient / std_error
    countries = int(result.entity_info["total"])
    degrees_of_freedom = countries - 1
    critical_value = float(student_t.ppf(0.975, degrees_of_freedom))
    return {
        "model": model_name,
        "coefficient": coefficient,
        "std_error": std_error,
        "t_stat": t_stat,
        "p_value": float(2 * student_t.sf(abs(t_stat), degrees_of_freedom)),
        "ci_lower": coefficient - critical_value * std_error,
        "ci_upper": coefficient + critical_value * std_error,
        "observations": int(result.nobs),
        "countries": countries,
        "within_r2": float(result.rsquared_within),
    }


def fit_models(model_data: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Fit country FE and country-plus-month FE models with country clustering."""
    indexed = model_data.set_index(["country", "date"])
    country_fe = PanelOLS.from_formula(
        "hicp_annual_rate ~ 1 + unemployment_lag6 + EntityEffects",
        data=indexed,
    ).fit(cov_type="clustered", cluster_entity=True, group_debias=True)
    two_way_fe = PanelOLS.from_formula(
        "hicp_annual_rate ~ 1 + unemployment_lag6 + EntityEffects + TimeEffects",
        data=indexed,
    ).fit(cov_type="clustered", cluster_entity=True, group_debias=True)

    table = pd.DataFrame(
        [
            _tidy_result(country_fe, "Country fixed effects"),
            _tidy_result(two_way_fe, "Country + month fixed effects"),
        ]
    )
    return table, {"country_fe": country_fe, "two_way_fe": two_way_fe}


def descriptive_summary(panel: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    monthly = (
        panel.groupby("date", as_index=False)
        .agg(
            mean_inflation=("hicp_annual_rate", "mean"),
            median_inflation=("hicp_annual_rate", "median"),
            mean_unemployment=("unemployment_rate", "mean"),
        )
        .sort_values("date")
    )
    peak = monthly.loc[monthly["mean_inflation"].idxmax()]

    def period_mean(start: str, end: str) -> float:
        selected = panel[panel["date"].between(start, end)]
        return float(selected["hicp_annual_rate"].mean())

    summary = {
        "peak_month": peak["date"].strftime("%Y-%m"),
        "peak_mean_inflation": float(peak["mean_inflation"]),
        "mean_inflation_2010_2019": period_mean("2010-01-01", "2019-12-01"),
        "mean_inflation_2021_2023": period_mean("2021-01-01", "2023-12-01"),
        "mean_inflation_2025": period_mean("2025-01-01", "2025-12-01"),
    }
    return monthly, summary
