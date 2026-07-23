from pathlib import Path

import pandas as pd


RBI_INFLATION_TARGET = 4.0
DEFAULT_LOOKBACK_QUARTERS = 4

INFLATION_DATA_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "india_quarterly_inflation.csv"
)


def load_inflation_history():
    """Load the complete official quarterly inflation history."""
    history = pd.read_csv(INFLATION_DATA_PATH)

    history["Inflation"] = pd.to_numeric(
        history["Inflation"],
        errors="coerce",
    )

    history["Quarter No"] = range(1, len(history) + 1)

    return history


def calculate_inflation_baseline(
    data=None,
    periods=DEFAULT_LOOKBACK_QUARTERS,
):
    """
    Calculate an automatic baseline from recent observed inflation.

    If inflation data is unavailable, use the RBI's 4% target.
    """
    if data is None:
        data = load_inflation_history()

    if "Inflation" not in data.columns:
        return {
            "baseline": RBI_INFLATION_TARGET,
            "latest": None,
            "quarters": [],
            "method": "RBI target fallback",
        }

    history = data[
        ["Quarter", "Quarter No", "Inflation"]
    ].copy()

    history["Inflation"] = pd.to_numeric(
        history["Inflation"],
        errors="coerce",
    )

    history = (
        history.dropna(subset=["Inflation"])
        .sort_values("Quarter No")
        .tail(periods)
    )

    if history.empty:
        return {
            "baseline": RBI_INFLATION_TARGET,
            "latest": None,
            "quarters": [],
            "method": "RBI target fallback",
        }

    return {
        "baseline": round(
            float(history["Inflation"].mean()),
            2,
        ),
        "latest": round(
            float(history["Inflation"].iloc[-1]),
            2,
        ),
        "quarters": history["Quarter"].tolist(),
        "method": (
            f"Average of latest {len(history)} observed quarters"
        ),
    }