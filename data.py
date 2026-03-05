import os
import warnings
from datetime import datetime, timedelta

import numpy as np
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

SECTOR_ETFS = [
    "SPY", "QQQ", "DIA", "IWM",
    "XLK", "XLF", "XLE", "XLV", "XLI", "XLC",
    "XLY", "XLP", "XLU", "XLRE", "XLB",
]


def get_all_fred_data() -> pd.DataFrame:
    frames = {}
    for name, series_id in FRED_SERIES.items():
        frames[name] = fred.get_series(series_id, observation_start=FIVE_YEARS_AGO)
    df = pd.DataFrame(frames)
    df.index.name = "date"
    return df


def compute_yield_spread(df: pd.DataFrame) -> pd.Series:
    return df["10-Year Treasury"] - df["2-Year Treasury"]


def get_sector_data() -> pd.DataFrame:
    tickers = " ".join(SECTOR_ETFS)
    data = yf.download(tickers, start=FIVE_YEARS_AGO, end=TODAY)
    if isinstance(data.columns, pd.MultiIndex):
        data = data["Close"]
    if data.index.tz is not None:
        data.index = data.index.tz_localize(None)
    return data


def compute_sector_returns(prices: pd.DataFrame, period: str = "YTD") -> pd.Series:
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


def compute_macro_correlations(df: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Pearson correlation between each FRED indicator and
    SPY's monthly return over the same month.
    Returns a DataFrame with correlation values and interpretation labels.
    """
    # Monthly SPY returns
    spy_monthly = prices["SPY"].resample("ME").last().pct_change().dropna() * 100

    indicator_cols = [
        "CPI Inflation (Trimmed Mean)",
        "Federal Funds Rate",
        "VIX",
        "High Yield Spread",
        "Consumer Sentiment",
        "Unemployment Rate",
    ]

    # Yield spread computed separately
    spread = compute_yield_spread(df)

    results = {}
    for col in indicator_cols:
        series = df[col].resample("ME").last().dropna()
        combined = pd.concat([series, spy_monthly], axis=1).dropna()
        if len(combined) < 12:
            continue
        corr = combined.iloc[:, 0].corr(combined.iloc[:, 1])
        results[col] = round(corr, 3)

    # Add yield spread
    spread_monthly = spread.resample("ME").last().dropna()
    combined = pd.concat([spread_monthly, spy_monthly], axis=1).dropna()
    if len(combined) >= 12:
        results["Yield Curve (10Y-2Y)"] = round(
            combined.iloc[:, 0].corr(combined.iloc[:, 1]), 3
        )

    corr_df = pd.DataFrame.from_dict(
        results, orient="index", columns=["Correlation"]
    ).sort_values("Correlation")

    # Friendly display names
    name_map = {
        "CPI Inflation (Trimmed Mean)": "Inflation",
        "Federal Funds Rate": "Fed Rate",
        "VIX": "VIX (Fear Index)",
        "High Yield Spread": "Credit Spread",
        "Consumer Sentiment": "Consumer Sentiment",
        "Unemployment Rate": "Unemployment",
        "Yield Curve (10Y-2Y)": "Yield Curve",
    }
    corr_df.index = [name_map.get(i, i) for i in corr_df.index]
    return corr_df


def get_market_news(top_sector: str = None, bottom_sector: str = None,
                    vix_elevated: bool = False, max_articles: int = 10) -> list:
    """
    Fetch contextually relevant market news based on current conditions.
    Prioritizes: leading sector, lagging sector, broad market, Fed/macro if stressed.
    Each article is tagged with why it's relevant.
    """
    # Build a priority queue of (ticker, label) pairs
    targets = [("SPY", "Broad Market")]
    if top_sector:
        targets.insert(0, (top_sector, f"Leading Sector — why {top_sector} is up"))
    if bottom_sector:
        targets.insert(1, (bottom_sector, f"Lagging Sector — why {bottom_sector} is down"))
    if vix_elevated:
        targets.append(("^VIX", "Market Volatility"))
    # Always include Fed/rates context
    targets.append(("TLT", "Bond Market / Fed Policy"))

    seen = set()
    articles = []
    now = datetime.utcnow()

    for ticker, label in targets:
        try:
            raw = yf.Ticker(ticker).news or []
        except Exception:
            continue
        for item in raw:
            content = item.get("content", {})
            title = content.get("title", "").strip()
            url = (content.get("canonicalUrl") or {}).get("url", "")
            source = (content.get("provider") or {}).get("displayName", "Yahoo Finance")
            pub_str = content.get("pubDate", "")
            if not title or not url or title in seen:
                continue
            seen.add(title)
            try:
                pub_dt = datetime.strptime(pub_str, "%Y-%m-%dT%H:%M:%SZ")
                delta = now - pub_dt
                hours = int(delta.total_seconds() // 3600)
                age = f"{hours}h ago" if hours < 24 else f"{delta.days}d ago"
                # Skip articles older than 3 days
                if delta.days > 3:
                    continue
            except Exception:
                age = ""
            articles.append({
                "title": title,
                "url": url,
                "source": source,
                "age": age,
                "label": label,
            })
            if len(articles) >= max_articles:
                return articles

    return articles


def compute_recession_score(df: pd.DataFrame) -> dict:
    """
    Composite recession risk score (0-100) from 5 signals.
    Higher = more recession risk.
    """
    score = 0
    signals = {}

    # 1. Yield curve inverted?
    spread = compute_yield_spread(df).dropna()
    spread_val = spread.iloc[-1]
    if spread_val < 0:
        score += 25
        signals["Yield Curve"] = ("Inverted — strong recession signal", "danger")
    elif spread_val < 0.5:
        score += 10
        signals["Yield Curve"] = ("Flattening — watch closely", "warning")
    else:
        signals["Yield Curve"] = ("Normal — no immediate concern", "success")

    # 2. Unemployment rising?
    unemp = df["Unemployment Rate"].dropna()
    unemp_3m_change = unemp.iloc[-1] - unemp.iloc[-4] if len(unemp) >= 4 else 0
    if unemp_3m_change > 0.5:
        score += 25
        signals["Unemployment Trend"] = ("Rising sharply — labor market weakening", "danger")
    elif unemp_3m_change > 0.1:
        score += 10
        signals["Unemployment Trend"] = ("Ticking up — early warning sign", "warning")
    else:
        signals["Unemployment Trend"] = ("Stable or falling — labor market healthy", "success")

    # 3. Credit spreads wide?
    hy = df["High Yield Spread"].dropna().iloc[-1]
    if hy > 6:
        score += 25
        signals["Credit Spreads"] = (f"Wide at {hy:.2f}% — markets pricing in stress", "danger")
    elif hy > 4:
        score += 10
        signals["Credit Spreads"] = (f"Elevated at {hy:.2f}% — some caution warranted", "warning")
    else:
        signals["Credit Spreads"] = (f"Tight at {hy:.2f}% — risk appetite healthy", "success")

    # 4. Consumer sentiment falling?
    sentiment = df["Consumer Sentiment"].dropna()
    sent_val = sentiment.iloc[-1]
    sent_6m_change = sent_val - sentiment.iloc[-7] if len(sentiment) >= 7 else 0
    if sent_6m_change < -10:
        score += 15
        signals["Consumer Sentiment"] = (f"Falling sharply ({sent_val:.0f}) — households worried", "danger")
    elif sent_6m_change < -4:
        score += 7
        signals["Consumer Sentiment"] = (f"Softening ({sent_val:.0f}) — mild concern", "warning")
    else:
        signals["Consumer Sentiment"] = (f"Stable ({sent_val:.0f}) — consumers confident", "success")

    # 5. VIX elevated?
    vix = df["VIX"].dropna().iloc[-1]
    if vix > 30:
        score += 10
        signals["Market Fear (VIX)"] = (f"Elevated at {vix:.1f} — panic in markets", "danger")
    elif vix > 20:
        score += 5
        signals["Market Fear (VIX)"] = (f"Cautious at {vix:.1f} — some anxiety", "warning")
    else:
        signals["Market Fear (VIX)"] = (f"Calm at {vix:.1f} — low fear", "success")

    return {"score": min(score, 100), "signals": signals}
