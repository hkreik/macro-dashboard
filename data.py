import os
import warnings
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf
from dotenv import load_dotenv
from fredapi import Fred

warnings.simplefilter(action="ignore", category=FutureWarning)

load_dotenv()
fred = Fred(api_key=os.getenv("FRED_API_KEY"))

FIVE_YEARS_AGO = (datetime.now() - timedelta(days=5 * 365)).strftime("%Y-%m-%d")
TODAY = datetime.now().strftime("%Y-%m-%d")

FRED_SERIES = {
    "Unemployment Rate": "UNRATE",
    "CPI Inflation (Trimmed Mean)": "PCETRIM12M159SFRBDAL",
    "Federal Funds Rate": "FEDFUNDS",
    "10-Year Treasury": "DGS10",
    "2-Year Treasury": "DGS2",
    "VIX": "VIXCLS",
    "High Yield Spread": "BAMLH0A0HYM2",
    "Consumer Sentiment": "UMCSENT",
}

# Sector SPDRs + major index ETFs
SECTOR_ETFS = [
    "SPY", "QQQ", "DIA", "IWM",
    "XLK", "XLF", "XLE", "XLV", "XLI", "XLC",
    "XLY", "XLP", "XLU", "XLRE", "XLB",
]


def get_all_fred_data() -> pd.DataFrame:
    """Fetch all FRED indicators into a single DataFrame."""
    frames = {}
    for name, series_id in FRED_SERIES.items():
        frames[name] = fred.get_series(series_id, observation_start=FIVE_YEARS_AGO)
    df = pd.DataFrame(frames)
    df.index.name = "date"
    return df


def compute_yield_spread(df: pd.DataFrame) -> pd.Series:
    """10-Year minus 2-Year Treasury yield spread."""
    return df["10-Year Treasury"] - df["2-Year Treasury"]


def get_sector_data() -> pd.DataFrame:
    """Download close prices for sector ETFs (5-year window)."""
    tickers = " ".join(SECTOR_ETFS)
    data = yf.download(tickers, start=FIVE_YEARS_AGO, end=TODAY)
    if isinstance(data.columns, pd.MultiIndex):
        data = data["Close"]
    if data.index.tz is not None:
        data.index = data.index.tz_localize(None)
    return data


def compute_sector_returns(prices: pd.DataFrame, period: str = "YTD") -> pd.Series:
    """Compute total return for each ETF over a given period."""
    lookbacks = {
        "1M": timedelta(days=30),
        "3M": timedelta(days=90),
        "6M": timedelta(days=182),
        "1Y": timedelta(days=365),
    }
    if period == "YTD":
        start = datetime(datetime.now().year, 1, 1)
    else:
        start = datetime.now() - lookbacks[period]

    mask = prices.index >= pd.Timestamp(start)
    if mask.sum() == 0:
        return pd.Series(dtype=float)

    start_prices = prices.loc[mask].iloc[0]
    end_prices = prices.iloc[-1]
    returns = ((end_prices - start_prices) / start_prices) * 100
    return returns.sort_values(ascending=False)


def compute_risk_return(prices: pd.DataFrame, period: str = "1Y") -> pd.DataFrame:
    """Annualized return and volatility for each ETF over a period."""
    import numpy as np
    lookbacks = {
        "3M": timedelta(days=90),
        "6M": timedelta(days=182),
        "1Y": timedelta(days=365),
    }
    start = datetime.now() - lookbacks.get(period, lookbacks["1Y"])
    mask = prices.index >= pd.Timestamp(start)
    sliced = prices.loc[mask].dropna(how="all")
    daily_returns = sliced.pct_change().dropna()

    trading_days = len(daily_returns)
    if trading_days == 0:
        return pd.DataFrame()

    ann_return = ((sliced.iloc[-1] / sliced.iloc[0]) ** (252 / trading_days) - 1) * 100
    ann_vol = daily_returns.std() * (252 ** 0.5) * 100
    sharpe = ann_return / ann_vol

    result = pd.DataFrame({
        "Return (%)": ann_return,
        "Volatility (%)": ann_vol,
        "Sharpe Ratio": sharpe,
    })
    return result.dropna()
