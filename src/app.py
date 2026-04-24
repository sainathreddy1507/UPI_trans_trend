from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from generate_data import main as generate_default_data


st.set_page_config(
    page_title="UPI Transaction Trend Dashboard",
    page_icon="📊",
    layout="wide",
)

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MONTHLY_FILE = DATA_DIR / "upi_monthly_trends.csv"
HOURLY_FILE = DATA_DIR / "upi_hourly_load_profile.csv"

if not MONTHLY_FILE.exists() or not HOURLY_FILE.exists():
    generate_default_data()


@st.cache_data
def load_monthly() -> pd.DataFrame:
    df = pd.read_csv(MONTHLY_FILE, parse_dates=["month"])
    df["year"] = df["month"].dt.year
    df["month_name"] = df["month"].dt.strftime("%b")
    return df


@st.cache_data
def load_hourly() -> pd.DataFrame:
    return pd.read_csv(HOURLY_FILE, parse_dates=["month"])


monthly = load_monthly()
hourly = load_hourly()

st.title("UPI Transaction Trend Analysis Dashboard")
st.caption(
    "Focus: transaction growth, technical failures, and peak-load stress windows "
    "for resilient digital payment operations."
)

st.sidebar.header("Filter View")
selected_years = st.sidebar.multiselect(
    "Select years",
    options=sorted(monthly["year"].unique().tolist()),
    default=sorted(monthly["year"].unique().tolist())[-4:],
)

if not selected_years:
    st.warning("Please select at least one year.")
    st.stop()

f_monthly = monthly[monthly["year"].isin(selected_years)].copy()
f_hourly = hourly[hourly["month"].dt.year.isin(selected_years)].copy()

latest = f_monthly.sort_values("month").iloc[-1]
prev = f_monthly.sort_values("month").iloc[-2]
mom_growth = ((latest["transaction_volume_mn"] - prev["transaction_volume_mn"]) / prev["transaction_volume_mn"]) * 100

c1, c2, c3, c4 = st.columns(4)
c1.metric("Latest Volume (Mn Txns)", f"{latest['transaction_volume_mn']:,.0f}", f"{mom_growth:+.2f}% MoM")
c2.metric("Latest Value (Cr INR)", f"{latest['transaction_value_cr']:,.0f}")
c3.metric("Success Rate", f"{latest['success_rate_pct']:.2f}%")
c4.metric("Technical Failure", f"{latest['technical_failure_rate_pct']:.2f}%")

st.markdown("### 1) Transaction Growth Trend")
fig_volume = go.Figure()
fig_volume.add_trace(
    go.Scatter(
        x=f_monthly["month"],
        y=f_monthly["transaction_volume_mn"],
        mode="lines+markers",
        name="Volume (Mn)",
        line={"width": 3},
    )
)
fig_volume.add_trace(
    go.Scatter(
        x=f_monthly["month"],
        y=f_monthly["transaction_value_cr"] / 1000,
        mode="lines",
        name="Value (Thousand Cr INR)",
        yaxis="y2",
        line={"dash": "dot"},
    )
)
fig_volume.update_layout(
    xaxis_title="Month",
    yaxis_title="Volume (Mn)",
    yaxis2={
        "title": "Value (Thousand Cr INR)",
        "overlaying": "y",
        "side": "right",
    },
    legend={"orientation": "h", "y": 1.08},
    height=420,
)
st.plotly_chart(fig_volume, use_container_width=True)

st.markdown("### 2) Payment Success and Failures")
c5, c6 = st.columns(2)

with c5:
    fig_success = px.line(
        f_monthly,
        x="month",
        y=["success_rate_pct", "technical_failure_rate_pct", "bank_failure_rate_pct"],
        labels={"value": "Rate (%)", "month": "Month", "variable": "Metric"},
    )
    fig_success.update_layout(height=380, legend_title_text="")
    st.plotly_chart(fig_success, use_container_width=True)

with c6:
    worst = f_monthly.nsmallest(8, "success_rate_pct")
    fig_worst = px.bar(
        worst,
        x="month",
        y="success_rate_pct",
        title="Lowest Success-Rate Months",
        text_auto=".2f",
    )
    fig_worst.update_layout(height=380, yaxis_title="Success Rate (%)", xaxis_title="Month")
    st.plotly_chart(fig_worst, use_container_width=True)

st.markdown("### 3) Peak Transaction Spikes (Hour-wise)")
agg_hour = (
    f_hourly.groupby("hour", as_index=False)
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
    labels={
        "avg_hourly_volume_mn": "Avg Hourly Volume (Mn)",
        "avg_hourly_tech_fail_pct": "Tech Failure (%)",
    },
)
fig_hourly.update_layout(height=420)
st.plotly_chart(fig_hourly, use_container_width=True)

peak_hours = agg_hour.nlargest(3, "avg_hourly_volume_mn")["hour"].tolist()
st.info(
    f"Peak load window observed around hours: {peak_hours}. "
    "Use this for autoscaling, retry policies, and infra pre-warming."
)

st.markdown("### 4) Operational Insight Table")
insights = f_monthly.copy()
insights["load_risk_score"] = np.round(
    (100 - insights["success_rate_pct"]) * 2.2 + insights["transaction_volume_mn"] / insights["transaction_volume_mn"].max() * 10,
    2,
)
st.dataframe(
    insights[
        [
            "month",
            "transaction_volume_mn",
            "transaction_value_cr",
            "success_rate_pct",
            "technical_failure_rate_pct",
            "bank_failure_rate_pct",
            "load_risk_score",
        ]
    ].sort_values("load_risk_score", ascending=False),
    use_container_width=True,
    hide_index=True,
)

st.markdown("---")
st.markdown(
    """
**Data Notes**
- Dataset is generated from publicly observed UPI growth patterns and failure-rate ranges.
- Use `src/fetch_public_data.py` to ingest monthly releases from free public sources and replace generated values.
- Suggested public sources: NPCI UPI product statistics and RBI payment system indicators.
"""
)
