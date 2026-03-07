"""
Tests for charts.py - verifies all chart builders return valid Plotly figures.
"""

import numpy as np
import pandas as pd
import pytest
from plotly.graph_objects import Figure

from charts import (
    correlation_chart,
    fed_policy_chart,
    sector_bar_chart,
    sp500_sma_chart,
    stress_chart,
)


@pytest.fixture()
def spy_prices():
    dates = pd.date_range("2019-01-01", periods=500, freq="B")
    rng = np.random.default_rng(1)
    returns = rng.normal(0.0004, 0.01, len(dates))
    return pd.Series(100 * np.cumprod(1 + returns), index=dates, name="SPY")


@pytest.fixture()
def vix_series():
    dates = pd.date_range("2020-01-01", periods=60, freq="ME")
    return pd.Series(np.random.default_rng(2).uniform(12, 40, 60), index=dates)


@pytest.fixture()
def hy_spread():
    dates = pd.date_range("2020-01-01", periods=60, freq="ME")
    return pd.Series(np.random.default_rng(3).uniform(2.5, 8.0, 60), index=dates)


@pytest.fixture()
def sample_fred_df():
    dates = pd.date_range("2020-01-01", periods=60, freq="ME")
    rng = np.random.default_rng(4)
    return pd.DataFrame(
        {
            "CPI Inflation (Trimmed Mean)": rng.uniform(1.5, 5.0, 60),
            "Federal Funds Rate": rng.uniform(0.0, 5.5, 60),
        },
        index=dates,
    )


@pytest.fixture()
def sample_returns():
    tickers = ["SPY", "QQQ", "XLK", "XLF", "XLE", "XLV"]
    values = np.random.default_rng(5).uniform(-10, 20, len(tickers))
    return pd.Series(values, index=tickers).sort_values(ascending=False)


@pytest.fixture()
def sample_corr_df():
    return pd.DataFrame({
        "Indicator": ["VIX", "High Yield Spread", "CPI Inflation (Trimmed Mean)", "Consumer Sentiment"],
        "Correlation": [-0.59, -0.28, 0.05, 0.31],
        "Direction": ["Negative", "Negative", "Neutral", "Positive"],
    })


class TestSp500SmaChart:
    def test_returns_figure(self, spy_prices):
        assert isinstance(sp500_sma_chart(spy_prices), Figure)

    def test_has_three_traces(self, spy_prices):
        assert len(sp500_sma_chart(spy_prices).data) == 3

    def test_trace_names(self, spy_prices):
        names = [t.name for t in sp500_sma_chart(spy_prices).data]
        assert "SPY" in names and "50-Day SMA" in names and "200-Day SMA" in names

    def test_handles_short_series(self):
        dates = pd.date_range("2024-01-01", periods=50, freq="B")
        short = pd.Series(100 + np.random.default_rng(6).normal(0, 1, 50).cumsum(), index=dates)
        assert isinstance(sp500_sma_chart(short), Figure)


class TestStressChart:
    def test_returns_figure(self, vix_series, hy_spread):
        assert isinstance(stress_chart(vix_series, hy_spread), Figure)

    def test_has_two_traces(self, vix_series, hy_spread):
        assert len(stress_chart(vix_series, hy_spread).data) == 2

    def test_handles_misaligned_dates(self):
        vix = pd.Series([20, 25, 18], index=pd.date_range("2024-01-01", periods=3, freq="ME"))
        hy = pd.Series([4.5, 5.0], index=pd.date_range("2024-02-01", periods=2, freq="ME"))
        assert isinstance(stress_chart(vix, hy), Figure)


class TestFedPolicyChart:
    def test_returns_figure(self, sample_fred_df):
        assert isinstance(fed_policy_chart(sample_fred_df), Figure)

    def test_has_two_traces(self, sample_fred_df):
        assert len(fed_policy_chart(sample_fred_df).data) == 2


class TestSectorBarChart:
    @pytest.mark.parametrize("period", ["YTD", "1M", "3M", "6M", "1Y"])
    def test_returns_figure_for_all_periods(self, sample_returns, period):
        assert isinstance(sector_bar_chart(sample_returns, period), Figure)

    def test_title_includes_period(self, sample_returns):
        assert "3M" in sector_bar_chart(sample_returns, "3M").layout.title.text

    def test_bar_count_matches_input(self, sample_returns):
        assert len(sector_bar_chart(sample_returns, "YTD").data[0].x) == len(sample_returns)


class TestCorrelationChart:
    def test_returns_figure(self, sample_corr_df):
        assert isinstance(correlation_chart(sample_corr_df), Figure)

    def test_is_horizontal_bar(self, sample_corr_df):
        assert correlation_chart(sample_corr_df).data[0].orientation == "h"

    def test_bar_count_matches_dataframe(self, sample_corr_df):
        assert len(correlation_chart(sample_corr_df).data[0].y) == len(sample_corr_df)
