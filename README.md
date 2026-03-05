# Macro-Equity Dashboard

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
- **Recession Risk Score** — a composite 0–100 score built from 5 historically reliable signals (yield curve, unemployment trend, credit spreads, consumer sentiment, VIX)
- **Correlation Analysis** — Pearson correlations between 7 macro indicators and monthly S&P 500 returns, computed across 60 months of data to identify which FRED series have a statistically meaningful relationship with market performance

---

## Data Sources

| Source | What it provides |
|--------|-----------------|
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
Pearson correlation measures the linear relationship between two variables on a -1 to +1 scale. I computed it between monthly values of each FRED indicator and the S&P 500's return that same month, over a 60-month window. This gives a data-driven answer to the question: *which macro variables actually move with the market?* The result — VIX at -0.59, credit spreads at -0.28 — confirms what finance theory predicts: fear and stress indicators move opposite to equity returns.

**Why the 200-day moving average as the trend signal?**
The 200-day SMA is the single most widely used trend indicator among professional investors. When price is above it, the market is considered to be in an uptrend; below it, a downtrend. It filters out short-term noise and reflects the underlying momentum over approximately one trading year.

**Why a composite recession score instead of a single indicator?**
No single indicator reliably predicts recessions. The yield curve is the most historically accurate, but it has produced false positives. By combining the yield curve, unemployment trend, credit spreads, consumer sentiment, and VIX into a weighted score, the dashboard reduces noise and provides a more robust risk gauge — similar to how the Conference Board constructs its Leading Economic Index.

---

## Running Locally

```bash
git clone https://github.com/YOUR_USERNAME/macro-dashboard.git
cd macro-dashboard
pip install -r requirements.txt
```

Create a `.env` file:
```
FRED_API_KEY=your_key_here
```

Get a free FRED API key at [research.stlouisfed.org/fred2](https://research.stlouisfed.org/fred2/).

```bash
python app.py
```

Open [http://127.0.0.1:8050](http://127.0.0.1:8050).

---

## Project Structure

```
macro-dashboard/
├── app.py          # Dash layout, callbacks, and narrative generation
├── data.py         # FRED + Yahoo Finance data fetching and computation
├── charts.py       # Plotly chart builders
├── requirements.txt
└── render.yaml     # Render deployment config
```
