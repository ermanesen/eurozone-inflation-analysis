"""Publication-ready figures for the project."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


BLUE = "#2457A7"
ORANGE = "#D97706"
INK = "#172033"
GRID = "#D9E1EC"


def _style() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 130,
            "font.size": 10,
            "axes.titleweight": "bold",
            "axes.edgecolor": GRID,
            "axes.labelcolor": INK,
            "text.color": INK,
            "xtick.color": INK,
            "ytick.color": INK,
        }
    )


def save_trend_figure(monthly: pd.DataFrame, output: str | Path) -> None:
    _style()
    fig, ax = plt.subplots(figsize=(11, 5.6))
    ax.plot(monthly["date"], monthly["mean_inflation"], color=BLUE, linewidth=2.4)
    ax.axhline(2, color=ORANGE, linestyle="--", linewidth=1.4, label="2% reference")
    ax.axvspan(pd.Timestamp("2020-03-01"), pd.Timestamp("2020-12-01"), color="#94A3B8", alpha=0.15)
    ax.axvspan(pd.Timestamp("2022-02-01"), pd.Timestamp("2023-12-01"), color="#F59E0B", alpha=0.10)
    ax.set(title="Average annual HICP inflation across eight euro-area economies", ylabel="Annual rate of change (%)", xlabel="")
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(output, format="svg", bbox_inches="tight")
    plt.close(fig)


def _two_way_demean(frame: pd.DataFrame, column: str) -> pd.Series:
    return (
        frame[column]
        - frame.groupby("country")[column].transform("mean")
        - frame.groupby("date")[column].transform("mean")
        + frame[column].mean()
    )


def save_partial_scatter(model_data: pd.DataFrame, coefficient: float, output: str | Path) -> None:
    _style()
    frame = model_data.copy()
    x = _two_way_demean(frame, "unemployment_lag6")
    y = _two_way_demean(frame, "hicp_annual_rate")
    fig, ax = plt.subplots(figsize=(8, 5.6))
    ax.scatter(x, y, s=11, alpha=0.18, color=BLUE, edgecolors="none")
    line_x = np.linspace(x.quantile(0.01), x.quantile(0.99), 100)
    ax.plot(line_x, coefficient * line_x, color=ORANGE, linewidth=2.2)
    ax.axhline(0, color=GRID, linewidth=0.8)
    ax.axvline(0, color=GRID, linewidth=0.8)
    ax.set(
        title="Phillips-curve partial relationship after country and month effects",
        xlabel="Six-month-lagged unemployment, residualized (pp)",
        ylabel="Annual HICP inflation, residualized (pp)",
    )
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, format="svg", bbox_inches="tight")
    plt.close(fig)


def save_coefficient_figure(results: pd.DataFrame, output: str | Path) -> None:
    _style()
    frame = results.iloc[::-1].reset_index(drop=True)
    y = np.arange(len(frame))
    lower = frame["coefficient"] - frame["ci_lower"]
    upper = frame["ci_upper"] - frame["coefficient"]
    fig, ax = plt.subplots(figsize=(8, 3.7))
    ax.errorbar(
        frame["coefficient"],
        y,
        xerr=np.vstack([lower, upper]),
        fmt="o",
        color=BLUE,
        ecolor=BLUE,
        capsize=4,
        markersize=7,
    )
    ax.axvline(0, color=ORANGE, linestyle="--", linewidth=1.3)
    ax.set_yticks(y, frame["model"])
    ax.set(
        title="Estimated effect of a 1 pp increase in lagged unemployment",
        xlabel="Change in annual HICP inflation (percentage points)",
    )
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.spines[["top", "right", "left"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, format="svg", bbox_inches="tight")
    plt.close(fig)
