# Macro-Equity Dashboard

[![CI](https://github.com/hkreik/macro-dashboard/actions/workflows/ci.yml/badge.svg)](https://github.com/hkreik/macro-dashboard/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A live macro-economic dashboard that tracks key Federal Reserve data and equity market indicators, synthesizes them into plain-English analysis, and identifies which macro variables have historically moved the S&P 500.

**Live demo:** *(add your Render URL here once deployed)*

---

## What It Does

The dashboard answers four questions in real time:

1. **Is the market trending up or down?** — S&P 500 price vs. 50-day and 200-day moving averages
2. **How much stress is in the system?** — VIX fear index overlaid with high-yield credit spreads
3. **What is the Fed doing and why?** — Inflation vs. Federal Funds Rate over 5 years
4. **Where is money flowing?** — Sector ETF returns across 1M, 3M, 6M, YTD, and 1Y periods

It also includes:

- **Market Briefing** — auto-generated plain-English summary of current conditions, updated from live data on every page load
- **Recession Risk Score** — a composite 0-100 score built from 5 historically reliable signals (yield curve, unemployment trend, credit spreads, consumer sentiment, VIX)
- **Correlation Analysis** — Pearson correlations between 7 macro indicators and monthly S&P 500 returns over 60 months

---

## Data Sources

| Source | What it provides |
|---------|------------------|
| [FRED (Federal Reserve Economic Data)](https://fred.stlouisfed.org/) | Inflation, Fed Funds Rate, Unemployment, Yield Curve, VIX, Credit Spreads, Consumer Sentiment |
| [Yahoo Finance](https://finance.yahoo.com/) | Daily closing prices for SPY, QQQ, DIA, IWM, and 11 sector ETFs |

Data is cached for 1 hour per session.

---

## Technical Stack

- **Python 3.11**
- **Dash / Plotly** — interactive charts and reactive layout
- **pandas / numpy** — data wrangling and statistical analysis
- **fredapi** — FRED API client
- **yfinance** — Yahoo Finance market data
- **Flask-Caching** — 1-hour server-side cache to reduce API calls
- **Gunicorn** — production WSGI server
- **Render** — cloud deployment

---

## Key Analytical Decisions

**Why Pearson correlation for the macro analysis?**
Pearson correlation measures the linear relationship between two variables on a -1 to +1 scale. Computed between monthly FRED indicators and SPY returns over 60 months — VIX at -0.59, credit spreads at -0.28 confirms that fear and stress indicators move opposite to equity returns.

**Why the 200-day moving average as the trend signal?**
The 200-day SMA is the most widely used trend indicator among professional investors. It filters out short-term noise and reflects the true medium-term trend.

**Why a composite Recession Risk Score?**
No single indicator reliably predicts recessions. By combining 5 signals (yield curve inversion, unemployment trend, credit spreads, consumer sentiment, VIX), the score reduces false positives and captures multiple dimensions of economic stress.

---

## Local Development

### Prerequisites
- Python 3.11
- A free [FRED API key](https://fred.stlouisfed.org/docs/api/api_key.html)

### Setup

```bash
git clone https://github.com/hkreik/macro-dashboard.git
cd macro-dashboard
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Create a `.env` file (see `.env.example`):
```
FRED_API_KEY=your_key_here
```

Install pre-commit hooks:
```bash
pre-commit install
```

Run locally:
```bash
python app.py
```

Open http://localhost:8050

### Running Tests

```bash
pytest                              # run all tests
pytest --cov=. --cov-report=html    # with HTML coverage report
```

### Linting

```bash
ruff check .     # lint
ruff format .    # auto-format
```

---

## CI/CD

Every push triggers GitHub Actions (`.github/workflows/ci.yml`) which:

1. Installs all dependencies
2. Runs `ruff check` and `ruff format --check`
3. Runs `pytest` with coverage (fails if below 70%)
4. Uploads coverage to Codecov

---

## Deployment (Render)

1. Push to GitHub
2. Connect repo to [Render](https://render.com)
3. Set `FRED_API_KEY` in Render environment variables
4. Deploy — `render.yaml` handles the rest

---

## Project Structure

```
macro-dashboard/
├── .github/
│   └── workflows/
│       └── ci.yml           # GitHub Actions CI pipeline
├── tests/
│   ├── __init__.py
│   ├── test_data.py         # Tests for data analytics functions
│   └── test_charts.py       # Tests for Plotly chart builders
├── app.py                   # Dash app, layout, callbacks
├── data.py                  # Data fetching (FRED + yfinance) and analytics
├── charts.py                # Plotly chart builders
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Dev dependencies (pytest, ruff, pre-commit)
├── ruff.toml                # Ruff linter/formatter config
├── pytest.ini               # Pytest config
├── .pre-commit-config.yaml  # Pre-commit hooks
├── .env.example             # Environment variable template
└── render.yaml              # Render deployment config
```
