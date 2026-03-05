import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

TEMPLATE = "plotly_dark"
HEIGHT = 420


# ── Chart 1: S&P 500 with 50/200 SMA ─────────────────────────────────────────

def sp500_sma_chart(spy_prices: pd.Series) -> go.Figure:
    spy = spy_prices.dropna()
    sma50 = spy.rolling(50).mean()
    sma200 = spy.rolling(200).mean()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=spy.index, y=spy.values,
        name="SPY", line=dict(color="#636EFA", width=1.5),
    ))
    fig.add_trace(go.Scatter(
        x=sma50.index, y=sma50.values,
        name="50-Day SMA", line=dict(color="#FECB52", width=1.5, dash="dot"),
    ))
    fig.add_trace(go.Scatter(
        x=sma200.index, y=sma200.values,
        name="200-Day SMA", line=dict(color="#EF553B", width=1.5, dash="dot"),
    ))
    fig.update_layout(
        title="Is the Market Trending Up or Down?",
        yaxis_title="Price ($)",
        template=TEMPLATE, height=HEIGHT,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        hovermode="x unified",
        margin=dict(t=60, b=40),
    )
    return fig


# ── Chart 2: System Stress — VIX + Credit Spread ─────────────────────────────

def stress_chart(vix: pd.Series, hy_spread: pd.Series) -> go.Figure:
    vix = vix.dropna()
    hy = hy_spread.dropna()

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=vix.index, y=vix.values,
            name="VIX (Fear Index)",
            line=dict(color="#AB63FA", width=2),
            fill="tozeroy", fillcolor="rgba(171,99,250,0.1)",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=hy.index, y=hy.values,
            name="High Yield Credit Spread (%)",
            line=dict(color="#EF553B", width=2),
        ),
        secondary_y=True,
    )

    fig.add_hrect(
        y0=30, y1=max(vix.max() * 1.1, 50),
        fillcolor="#EF553B", opacity=0.07,
        line_width=0,
        annotation_text="Panic Zone (VIX > 30)",
        annotation_position="top left",
        secondary_y=False,
    )

    fig.update_layout(
        title="How Much Stress Is in the System?",
        template=TEMPLATE, height=HEIGHT,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        hovermode="x unified",
        margin=dict(t=60, b=40),
    )
    fig.update_yaxes(title_text="VIX Level", secondary_y=False)
    fig.update_yaxes(title_text="Credit Spread (%)", secondary_y=True)
    return fig


# ── Chart 3: Fed Policy — Inflation + Fed Rate ────────────────────────────────

def fed_policy_chart(df: pd.DataFrame) -> go.Figure:
    inflation = df["CPI Inflation (Trimmed Mean)"].dropna()
    fed_rate = df["Federal Funds Rate"].dropna()

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=inflation.index, y=inflation.values,
            name="Inflation (%)",
            line=dict(color="#00CC96", width=2),
            fill="tozeroy", fillcolor="rgba(0,204,150,0.1)",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=fed_rate.index, y=fed_rate.values,
            name="Fed Funds Rate (%)",
            line=dict(color="#EF553B", width=2),
        ),
        secondary_y=True,
    )
    fig.add_hline(
        y=2.0, line_dash="dash", line_color="rgba(255,255,255,0.4)",
        annotation_text="Fed 2% Target",
        annotation_position="top left",
        secondary_y=False,
    )

    fig.update_layout(
        title="What Is the Fed Doing and Why?",
        template=TEMPLATE, height=HEIGHT,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        hovermode="x unified",
        margin=dict(t=60, b=40),
    )
    fig.update_yaxes(title_text="Inflation (%)", secondary_y=False)
    fig.update_yaxes(title_text="Fed Funds Rate (%)", secondary_y=True)
    return fig


# ── Chart 4: Sector Returns Bar ───────────────────────────────────────────────

BENCHMARKS = {"SPY", "QQQ", "DIA", "IWM"}

ETF_LABELS = {
    "SPY": "SPY — S&P 500",
    "QQQ": "QQQ — Nasdaq 100 (Tech)",
    "DIA": "DIA — Dow Jones",
    "IWM": "IWM — Small Cap",
    "XLK": "XLK — Technology",
    "XLF": "XLF — Financials",
    "XLE": "XLE — Energy",
    "XLV": "XLV — Health Care",
    "XLI": "XLI — Industrials",
    "XLC": "XLC — Communication",
    "XLY": "XLY — Consumer Discretionary",
    "XLP": "XLP — Consumer Staples",
    "XLU": "XLU — Utilities",
    "XLRE": "XLRE — Real Estate",
    "XLB": "XLB — Materials",
}


def sector_bar_chart(returns: pd.Series, period_label: str) -> go.Figure:
    labeled_index = [ETF_LABELS.get(t, t) for t in returns.index]
    colors = [
        "#FECB52" if t in BENCHMARKS
        else ("#00CC96" if v >= 0 else "#EF553B")
        for t, v in zip(returns.index, returns.values)
    ]
    fig = go.Figure(go.Bar(
        x=returns.values, y=labeled_index,
        orientation="h", marker_color=colors,
        text=[f"{v:+.1f}%" for v in returns.values],
        textposition="outside",
    ))
    fig.update_layout(
        title=f"Where Is Money Flowing? ({period_label})",
        template=TEMPLATE, height=520,
        xaxis_title="Return (%)",
        yaxis=dict(autorange="reversed"),
        margin=dict(t=60, b=40, r=80),
    )
    return fig


# ── Chart 5: Macro Correlation Bar ───────────────────────────────────────────

def correlation_chart(corr_df: pd.DataFrame) -> go.Figure:
    corr = corr_df["Correlation"]
    colors = ["#00CC96" if v > 0 else "#EF553B" for v in corr.values]

    fig = go.Figure(go.Bar(
        x=corr.values,
        y=corr.index,
        orientation="h",
        marker_color=colors,
        text=[f"{v:+.2f}" for v in corr.values],
        textposition="outside",
    ))
    fig.add_vline(x=0, line_color="rgba(255,255,255,0.3)", line_width=1)
    fig.update_layout(
        title="Which Macro Indicators Move With the Market?",
        xaxis_title="Pearson Correlation with SPY Monthly Returns",
        template=TEMPLATE, height=420,
        margin=dict(t=60, b=40, r=80, l=160),
        xaxis=dict(range=[-0.7, 0.7]),
    )
    return fig
