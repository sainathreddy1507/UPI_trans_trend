# UPI Transaction Trend Analysis

Professional dashboard project for analyzing:
- UPI transaction volume growth trends
- payment success and technical failure rates
- peak transaction spikes and load-risk windows

This directly addresses the project statement:
**Digital payment failure rates and load management are critical as UPI transactions boom.**

## Outcome

A production-style interactive dashboard built with Streamlit:
- KPI cards for latest transaction and success metrics
- trend analysis (volume + value)
- technical/bank failure monitoring
- peak-hour load visualization
- load risk scoring table for operational planning

## Project Structure

```
UPI_trans_trend/
├── data/
│   ├── upi_monthly_trends.csv
│   └── upi_hourly_load_profile.csv
├── src/
│   ├── app.py
│   ├── generate_data.py
│   └── fetch_public_data.py
├── requirements.txt
└── README.md
```

## Data

### Included now (ready-to-run)
- Synthetic but realistic dataset generated from public UPI growth patterns and failure-rate bands.
- Covers monthly trends from 2018 onward and derived hourly load profile.

### Free public sources you can plug in
- [NPCI - UPI Product Statistics](https://www.npci.org.in/what-we-do/upi/product-statistics)
- [RBI - Payment System Indicators](https://www.rbi.org.in/)

Use `src/fetch_public_data.py` to merge your downloaded CSV extracts into model-ready format.

## Quick Start

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Generate datasets:

```bash
python src/generate_data.py
```

3. Launch dashboard:

```bash
streamlit run src/app.py
```

## Vercel Deployment Fix

Vercel requires a Python ASGI/WSGI entrypoint (`app`) and cannot directly run Streamlit as the primary runtime.

This repo now includes:
- `api/index.py` (FastAPI app entrypoint for Vercel)
- `vercel.json` (rewrites all routes to `/api/index`)

So Vercel can deploy a web dashboard endpoint successfully.

## Recommended Analysis Story (for presentation)

1. **UPI scaling:** show long-term transaction growth trend.
2. **Reliability lens:** track success vs technical failure rates.
3. **Stress pattern:** identify peak load hours and vulnerable months.
4. **Actionable operations:** use load risk score to prioritize infra hardening and incident response.

## Professional Extensions (optional)

- Add forecast module (Prophet/ARIMA) for next 12 months.
- Add anomaly detection for sudden failure spikes.
- Connect live monthly refresh pipeline from public source dumps.
- Export monthly leadership report as PDF.
