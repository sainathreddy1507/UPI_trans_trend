from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True, parents=True)


def merge_public_monthly_data(npci_csv_path: str, rbi_csv_path: str) -> pd.DataFrame:
    """
    Merge free/public CSV extracts into a model-ready monthly dataset.

    Expected columns in NPCI extract:
      - month
      - transaction_volume_mn
      - transaction_value_cr

    Expected columns in RBI extract:
      - month
      - success_rate_pct (or technical_failure_rate_pct + bank_failure_rate_pct)
      - technical_failure_rate_pct (optional)
      - bank_failure_rate_pct (optional)
    """
    npci = pd.read_csv(npci_csv_path, parse_dates=["month"])
    rbi = pd.read_csv(rbi_csv_path, parse_dates=["month"])

    out = npci.merge(rbi, on="month", how="left")

    if "success_rate_pct" not in out.columns:
        out["success_rate_pct"] = 100 - out["technical_failure_rate_pct"].fillna(0) - out["bank_failure_rate_pct"].fillna(0)

    if "technical_failure_rate_pct" not in out.columns:
        out["technical_failure_rate_pct"] = (100 - out["success_rate_pct"]) * 0.6
    if "bank_failure_rate_pct" not in out.columns:
        out["bank_failure_rate_pct"] = (100 - out["success_rate_pct"]) * 0.4

    out = out.sort_values("month").reset_index(drop=True)
    return out[
        [
            "month",
            "transaction_volume_mn",
            "transaction_value_cr",
            "success_rate_pct",
            "technical_failure_rate_pct",
            "bank_failure_rate_pct",
        ]
    ]


def main() -> None:
    print(
        "Use merge_public_monthly_data(npci_csv_path, rbi_csv_path) "
        "to generate data/upi_monthly_trends.csv from free sources."
    )


if __name__ == "__main__":
    main()
