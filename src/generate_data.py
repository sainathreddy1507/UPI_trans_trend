from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True, parents=True)


def build_monthly_dataset() -> pd.DataFrame:
    """Generate a realistic UPI trend series using public trend assumptions."""
    rng = np.random.default_rng(42)
    months = pd.date_range("2018-01-01", "2026-03-01", freq="MS")
    t = np.arange(len(months))

    # Approximate long-run volume growth pattern seen in public NPCI trend reports.
    base = 130 * np.exp(0.042 * t)  # in million transactions
    seasonality = 1 + 0.08 * np.sin((2 * np.pi * t / 12) - 0.7)
    noise = rng.normal(1.0, 0.02, len(t))
    volume_mn = base * seasonality * noise

    # Assume average ticket size gradually increases over time.
    avg_ticket = 1100 + (t * 18) + rng.normal(0, 40, len(t))
    value_cr = (volume_mn * 1_000_000 * avg_ticket) / 10_000_000

    # Failure rates: gradual improvements with occasional stress spikes.
    tech_decline = np.clip(
        1.9 - (0.008 * t) + 0.25 * np.sin(2 * np.pi * t / 6) + rng.normal(0, 0.08, len(t)),
        0.25,
        3.2,
    )
    bank_decline = np.clip(
        1.4 - (0.004 * t) + 0.18 * np.cos(2 * np.pi * t / 5) + rng.normal(0, 0.07, len(t)),
        0.2,
        2.5,
    )
    success_rate = np.clip(100 - tech_decline - bank_decline, 94.0, 99.7)

    # Inject known "load stress" months for analysis demos.
    stress_months = pd.to_datetime(["2020-11-01", "2022-10-01", "2023-11-01", "2025-11-01"])
    stress_mask = months.isin(stress_months)
    tech_decline[stress_mask] += 0.35
    success_rate[stress_mask] -= 0.28

    df = pd.DataFrame(
        {
            "month": months,
            "transaction_volume_mn": np.round(volume_mn, 2),
            "transaction_value_cr": np.round(value_cr, 2),
            "success_rate_pct": np.round(success_rate, 3),
            "technical_failure_rate_pct": np.round(tech_decline, 3),
            "bank_failure_rate_pct": np.round(bank_decline, 3),
        }
    )
    return df


def build_hourly_load(dataset: pd.DataFrame) -> pd.DataFrame:
    """
    Build an hour-level load profile mapped from the latest 24 months.
    Useful for identifying system pressure windows and staffing strategy.
    """
    latest = dataset.tail(24).copy()
    profile = np.array(
        [
            0.020,
            0.012,
            0.010,
            0.009,
            0.010,
            0.018,
            0.035,
            0.055,
            0.063,
            0.060,
            0.054,
            0.052,
            0.051,
            0.049,
            0.047,
            0.050,
            0.058,
            0.072,
            0.082,
            0.090,
            0.085,
            0.070,
            0.050,
            0.036,
        ]
    )
    profile = profile / profile.sum()

    rows = []
    for _, row in latest.iterrows():
        for hour, share in enumerate(profile):
            hour_volume = row["transaction_volume_mn"] * share
            stress = 0.12 if hour in [18, 19, 20] else 0.0
            hour_tech_fail = max(0.12, row["technical_failure_rate_pct"] + stress)
            rows.append(
                {
                    "month": row["month"],
                    "hour": hour,
                    "estimated_hourly_volume_mn": round(hour_volume, 4),
                    "estimated_hourly_technical_failure_rate_pct": round(hour_tech_fail, 3),
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    monthly = build_monthly_dataset()
    hourly = build_hourly_load(monthly)

    monthly.to_csv(DATA_DIR / "upi_monthly_trends.csv", index=False)
    hourly.to_csv(DATA_DIR / "upi_hourly_load_profile.csv", index=False)
    print("Generated:")
    print(f"- {DATA_DIR / 'upi_monthly_trends.csv'}")
    print(f"- {DATA_DIR / 'upi_hourly_load_profile.csv'}")


if __name__ == "__main__":
    main()
