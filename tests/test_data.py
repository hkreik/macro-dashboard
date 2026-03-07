"""
Tests for data.py - covers analytics functions that do NOT require
live API calls (FRED / yfinance). External I/O is mocked throughout.
"""

import numpy as np
import pandas as pd
import pytest

from data import (
    compute_macro_correlations,
    compute_recession_score,
    compute_sector_returns,
    compute_yield_spread,
)


@pytest.fixture()
def sample_fred_df():
    dates = pd.date_range("2020-01-01", periods=60, freq="ME")
    rng = np.random.default_rng(42)
    df = pd.DataFrame(
        {
            "Unemployment Rate": rng.uniform(3.5, 7.5, 60),
            "CPI Inflation (Trimmed Mean)": rng.uniform(1.5, 5.0, 60),
            "Federal Funds Rate": rng.uniform(0.0, 5.5, 60),
            "10-Year Treasury": rng.uniform(1.0, 5.0, 60),
            "2-Year Treasury": rng.uniform(0.5, 5.5, 60),
            "VIX": rng.uniform(12, 45, 60),
            "High Yield Spread": rng.uniform(2.5, 9.0, 60),
            "Consumer Sentiment": rng.uniform(50, 100, 60),
        },
        index=dates,
    )
    df.index.name = "date"
    return df


@pytest.fixture()
def sample_prices():
    dates = pd.date_range("2020-01-01", periods=1260, freq="B")
    rng = np.random.default_rng(99)
    tickers = ["SPY", "QQQ", "XLK", "XLF", "XLE"]
    data = {}
    for ticker in tickers:
        returns = rng.normal(0.0003, 0.012, len(dates))
        prices = 100 * np.cumprod(1 + returns)
        data[ticker] = prices
    df = pd.DataFrame(data, index=dates)
    df.index.name = "date"
    return df


class TestComputeYieldSpread:
    def test_returns_series(self, sample_fred_df):
        assert isinstance(compute_yield_spread(sample_fred_df), pd.Series)

    def test_length_matches_input(self, sample_fred_df):
        assert len(compute_yield_spread(sample_fred_df)) == len(sample_fred_df)

    def test_values_correct(self, sample_fred_df):
        expected = sample_fred_df["10-Year Treasury"] - sample_fred_df["2-Year Treasury"]
        pd.testing.assert_series_equal(compute_yield_spread(sample_fred_df), expected)

    def test_can_be_negative(self, sample_fred_df):
        df = sample_fred_df.copy()
        df["10-Year Treasury"] = 2.0
        df["2-Year Treasury"] = 4.0
        assert (compute_yield_spread(df) < 0).all()


class TestComputeSectorReturns:
    @pytest.mark.parametrize("period", ["YTD", "1M", "3M", "6M", "1Y"])
    def test_returns_series_for_all_periods(self, sample_prices, period):
        result = compute_sector_returns(sample_prices, period)
        assert isinstance(result, pd.Series)
        assert len(result) > 0

    def test_sorted_descending(self, sample_prices):
        result = compute_sector_returns(sample_prices, "1M")
        assert list(result.values) == sorted(result.values, reverse=True)

    def test_empty_on_insufficient_history(self):
        dates = pd.date_range("2024-01-01", periods=5, freq="B")
        tiny = pd.DataFrame({"SPY": [100, 101, 102, 103, 104]}, index=dates)
        assert isinstance(compute_sector_returns(tiny, "1Y"), pd.Series)


class TestComputeRecessionScore:
    def test_returns_dict_with_score_and_signals(self, sample_fred_df, sample_prices):
        result = compute_recession_score(sample_fred_df, sample_prices)
        assert "score" in result and "signals" in result

    def test_score_in_valid_range(self, sample_fred_df, sample_prices):
        assert 0 <= compute_recession_score(sample_fred_df, sample_prices)["score"] <= 100

    def test_high_risk_scenario(self, sample_fred_df, sample_prices):
        df = sample_fred_df.copy()
        df["10-Year Treasury"] = 2.0
        df["2-Year Treasury"] = 4.5
        df["Unemployment Rate"] = np.linspace(4.0, 7.0, len(df))
        df["High Yield Spread"] = 8.0
        df["Consumer Sentiment"] = 45.0
        df["VIX"] = 40.0
        assert compute_recession_score(df, sample_prices)["score"] >= 60

    def test_low_risk_scenario(self, sample_fred_df, sample_prices):
        df = sample_fred_df.copy()
        df["10-Year Treasury"] = 4.5
        df["2-Year Treasury"] = 2.0
        df["Unemployment Rate"] = np.linspace(5.0, 4.0, len(df))
        df["High Yield Spread"] = 3.0
        df["Consumer Sentiment"] = 90.0
        df["VIX"] = 15.0
        assert compute_recession_score(df, sample_prices)["score"] <= 35

    def test_signals_has_expected_keys(self, sample_fred_df, sample_prices):
        signals = compute_recession_score(sample_fred_df, sample_prices)["signals"]
        assert {"Yield Curve", "Unemployment Trend", "Credit Spreads", "Consumer Sentiment", "VIX"}.issubset(signals)


class TestComputeMacroCorrelations:
    def test_returns_dataframe(self, sample_fred_df, sample_prices):
        assert isinstance(compute_macro_correlations(sample_fred_df, sample_prices), pd.DataFrame)

    def test_has_required_columns(self, sample_fred_df, sample_prices):
        result = compute_macro_correlations(sample_fred_df, sample_prices)
        assert {"Indicator", "Correlation", "Direction"}.issubset(result.columns)

    def test_correlations_in_valid_range(self, sample_fred_df, sample_prices):
        result = compute_macro_correlations(sample_fred_df, sample_prices)
        assert (result["Correlation"].abs() <= 1.0).all()

    def test_direction_labels_valid(self, sample_fred_df, sample_prices):
        result = compute_macro_correlations(sample_fred_df, sample_prices)
        assert set(result["Direction"].unique()).issubset({"Positive", "Negative", "Neutral"})

    def test_sorted_descending(self, sample_fred_df, sample_prices):
        corrs = compute_macro_correlations(sample_fred_df, sample_prices)["Correlation"].tolist()
        assert corrs == sorted(corrs, reverse=True)
