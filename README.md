# Macro-Equity Dashboard

Interactive dashboard tracking US macroeconomic indicators alongside sector equity performance. Built with Python, Dash, and Plotly.

## Live Demo
[Deployed on Render](#) *(update with your Render URL)*

## Features
- 10 macroeconomic indicators from FRED (GDP, unemployment, CPI, yield curve, PMI, and more)
- 11 SPDR sector ETFs + SPY benchmark from Yahoo Finance
- Yield curve inversion tracking (recession indicator)
- Sector performance heatmap with multi-period comparison
- Interactive period selector for sector returns
- Dark theme, responsive layout
- Hourly data caching

## Setup
1. Clone the repo
2. Get a free FRED API key at https://fred.stlouisfed.org/docs/api/api_key.html
3. Create a `.env` file in the project root:
   ```
   FRED_API_KEY=your_key_here
   ```
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Run locally:
   ```
   python app.py
   ```
6. Open http://127.0.0.1:8050

## Deploy to Render
1. Push to GitHub
2. Connect repo in Render dashboard
3. Render auto-detects `render.yaml`
4. Add `FRED_API_KEY` in Environment tab
5. Deploy

## Tech Stack
Python | Dash | Plotly | pandas | fredapi | yfinance | Flask-Caching

## Data Sources
- [FRED](https://fred.stlouisfed.org/) (Federal Reserve Economic Data)
- [Yahoo Finance](https://finance.yahoo.com/) (via yfinance)
