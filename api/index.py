from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fastapi import FastAPI
from fastapi.responses import HTMLResponse


app = FastAPI(title="UPI Transaction Trend Analysis")

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MONTHLY_FILE = DATA_DIR / "upi_monthly_trends.csv"
HOURLY_FILE = DATA_DIR / "upi_hourly_load_profile.csv"


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    monthly = pd.read_csv(MONTHLY_FILE, parse_dates=["month"]).sort_values("month")
    hourly = pd.read_csv(HOURLY_FILE, parse_dates=["month"]).sort_values(["month", "hour"])
    return monthly, hourly


@app.get("/", response_class=HTMLResponse)
def dashboard() -> str:
    monthly, hourly = load_data()
    latest = monthly.iloc[-1]
    prev = monthly.iloc[-2]
    mom_growth = ((latest["transaction_volume_mn"] - prev["transaction_volume_mn"]) / prev["transaction_volume_mn"]) * 100

    fig_volume = go.Figure()
    fig_volume.add_trace(
        go.Scatter(
            x=monthly["month"],
            y=monthly["transaction_volume_mn"],
            mode="lines+markers",
            name="Volume (Mn)",
        )
    )
    fig_volume.add_trace(
        go.Scatter(
            x=monthly["month"],
            y=monthly["transaction_value_cr"] / 1000,
            mode="lines",
            name="Value (Thousand Cr INR)",
            yaxis="y2",
            line={"dash": "dot"},
        )
    )
    fig_volume.update_layout(
        title="Transaction Growth Trend",
        xaxis_title="Month",
        yaxis_title="Volume (Mn)",
        yaxis2={"title": "Value (Thousand Cr INR)", "overlaying": "y", "side": "right"},
        height=420,
    )

    fig_success = px.line(
        monthly,
        x="month",
        y=["success_rate_pct", "technical_failure_rate_pct", "bank_failure_rate_pct"],
        title="Payment Success and Failure Trends",
        labels={"value": "Rate (%)", "month": "Month", "variable": "Metric"},
    )
    fig_success.update_layout(height=380)

    agg_hour = (
        hourly.groupby("hour", as_index=False)
        .agg(
            avg_hourly_volume_mn=("estimated_hourly_volume_mn", "mean"),
            avg_hourly_tech_fail_pct=("estimated_hourly_technical_failure_rate_pct", "mean"),
        )
    )
    fig_hourly = px.bar(
        agg_hour,
        x="hour",
        y="avg_hourly_volume_mn",
        color="avg_hourly_tech_fail_pct",
        color_continuous_scale="OrRd",
        title="Peak Transaction Spikes (Hour-wise)",
        labels={
            "avg_hourly_volume_mn": "Avg Hourly Volume (Mn)",
            "avg_hourly_tech_fail_pct": "Tech Failure (%)",
        },
    )
    fig_hourly.update_layout(height=420)

    html = f"""
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>UPI Transaction Trend Analysis</title>
        <style>
          body {{ font-family: Arial, sans-serif; margin: 24px; background: #f8fafc; color: #0f172a; }}
          h1 {{ margin-bottom: 8px; }}
          .kpi-wrap {{ display: grid; grid-template-columns: repeat(4, minmax(180px, 1fr)); gap: 12px; margin: 16px 0 20px; }}
          .kpi {{ background: white; border-radius: 10px; padding: 12px 14px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
          .kpi .label {{ color: #475569; font-size: 13px; }}
          .kpi .value {{ font-size: 24px; font-weight: 700; margin-top: 6px; }}
          .note {{ background: #e0f2fe; padding: 10px 12px; border-radius: 8px; margin: 8px 0 18px; }}
          .chart {{ background: white; padding: 10px; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,.08); margin-bottom: 14px; }}
        </style>
      </head>
      <body>
        <h1>UPI Transaction Trend Analysis Dashboard</h1>
        <p>Volume trends, technical failures, and peak transaction load behavior.</p>

        <div class="kpi-wrap">
          <div class="kpi"><div class="label">Latest Volume (Mn)</div><div class="value">{latest["transaction_volume_mn"]:,.0f}</div></div>
          <div class="kpi"><div class="label">MoM Growth</div><div class="value">{mom_growth:+.2f}%</div></div>
          <div class="kpi"><div class="label">Success Rate</div><div class="value">{latest["success_rate_pct"]:.2f}%</div></div>
          <div class="kpi"><div class="label">Technical Failure</div><div class="value">{latest["technical_failure_rate_pct"]:.2f}%</div></div>
        </div>

        <div class="note">
          Data source for this deployment is bundled project data.
          For free public monthly source updates, use NPCI and RBI extracts in the repo workflow.
        </div>

        <div class="chart">{fig_volume.to_html(full_html=False, include_plotlyjs="cdn")}</div>
        <div class="chart">{fig_success.to_html(full_html=False, include_plotlyjs=False)}</div>
        <div class="chart">{fig_hourly.to_html(full_html=False, include_plotlyjs=False)}</div>
      </body>
    </html>
    """
    return html
