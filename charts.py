import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

TEMPLATE = "plotly_dark"
HEIGHT = 420


# ── Chart 1: S&P 500 with 50/200 SMA ─────────────────────────────────────────

def sp500_sma_chart(spy_prices: pd.Series) -> go.Figure:
    """S&P 500 price with 50 and 200-day moving averages."""
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
        title="S&P 500 — Price & Moving Averages",
        yaxis_title="Price ($)",
        template=TEMPLATE, height=HEIGHT,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        hovermode="x unified",
        margin=dict(t=60, b=40),
    )
    return fig


# ── Chart 2: VIX Fear Gauge ──────────────────────────────────────────────────

def vix_chart(vix: pd.Series) -> go.Figure:
    """VIX with color zones: green (<20), yellow (20-30), red (>30)."""
    vix = vix.dropna()
    fig = go.Figure()
    # Background zones
    fig.add_hrect(y0=0, y1=20, fillcolor="#00CC96", opacity=0.08,
                  line_width=0, annotation_text="Low Fear",
                  annotation_position="top left")
    fig.add_hrect(y0=20, y1=30, fillcolor="#FECB52", opacity=0.08,
                  line_width=0, annotation_text="Elevated",
                  annotation_position="top left")
    fig.add_hrect(y0=30, y1=80, fillcolor="#EF553B", opacity=0.08,
                  line_width=0, annotation_text="High Fear / Panic",
                  annotation_position="top left")
    fig.add_trace(go.Scatter(
        x=vix.index, y=vix.values,
        name="VIX", line=dict(color="#AB63FA", width=2),
        fill="tozeroy", fillcolor="rgba(171,99,250,0.15)",
    ))
    fig.update_layout(
        title="VIX — Market Fear Index",
        yaxis_title="VIX Level",
        template=TEMPLATE, height=HEIGHT,
        hovermode="x unified",
        margin=dict(t=60, b=40),
        yaxis=dict(range=[0, max(vix.max() * 1.1, 40)]),
    )
    return fig


# ── Chart 3: Inflation ───────────────────────────────────────────────────────

def inflation_chart(inflation: pd.Series) -> go.Figure:
    """Trimmed Mean PCE inflation with 2% target."""
    inflation = inflation.dropna()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=inflation.index, y=inflation.values,
        fill="tozeroy", name="Trimmed Mean PCE (%)",
        line=dict(color="#00CC96", width=2),
    ))
    fig.add_hline(
        y=2.0, line_dash="dash", line_color="white",
        annotation_text="Fed 2% Target",
        annotation_position="top left",
    )
    fig.update_layout(
        title="Inflation — When Above 2%, Rates Stay High",
        yaxis_title="Rate (%)",
        template=TEMPLATE, height=HEIGHT,
        hovermode="x unified",
        margin=dict(t=60, b=40),
    )
    return fig


# ── Chart 4: Yield Curve Spread ───────────────────────────────────────────────

def yield_spread_chart(spread: pd.Series) -> go.Figure:
    """10Y-2Y spread with inversion warning."""
    spread = spread.dropna()
    fig = go.Figure()
    fig.add_hrect(y0=-3, y1=0, fillcolor="#EF553B", opacity=0.1,
                  line_width=0, annotation_text="Inverted = Recession Risk",
                  annotation_position="bottom left")
    fig.add_trace(go.Scatter(
        x=spread.index, y=spread.values,
        fill="tozeroy", name="10Y-2Y Spread",
        line=dict(color="#AB63FA", width=2),
    ))
    fig.add_hline(y=0, line_dash="solid", line_color="rgba(255,255,255,0.4)")
    fig.update_layout(
        title="Yield Curve — Inverts Before Every Recession",
        yaxis_title="Spread (pp)",
        template=TEMPLATE, height=HEIGHT,
        hovermode="x unified",
        margin=dict(t=60, b=40),
    )
    return fig


# ── Chart 5: Fed Funds vs Unemployment ────────────────────────────────────────

def fed_unemployment_chart(df: pd.DataFrame) -> go.Figure:
    """Fed Funds Rate vs Unemployment — shows the policy cycle."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=df.index, y=df["Unemployment Rate"],
            name="Unemployment (%)", line=dict(color="#636EFA"),
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df.index, y=df["Federal Funds Rate"],
            name="Fed Funds (%)", line=dict(color="#EF553B"),
        ),
        secondary_y=True,
    )
    fig.update_layout(
        title="The Fed's Balancing Act — Jobs vs. Rates",
        template=TEMPLATE, height=HEIGHT,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        hovermode="x unified",
        margin=dict(t=60, b=40),
    )
    fig.update_yaxes(title_text="Unemployment (%)", secondary_y=False)
    fig.update_yaxes(title_text="Fed Funds (%)", secondary_y=True)
    return fig


BENCHMARKS = {"SPY", "QQQ", "DIA", "IWM"}

ETF_COLORS = {
    "SPY": "#FECB52", "QQQ": "#00CC96", "DIA": "#636EFA", "IWM": "#EF553B",
    "XLK": "#AB63FA", "XLF": "#19D3F3", "XLE": "#FF6692", "XLV": "#B6E880",
    "XLI": "#FF97FF", "XLC": "#FFA15A", "XLY": "#FF6692", "XLP": "#72B7B2",
    "XLU": "#FECB52", "XLRE": "#636EFA", "XLB": "#EF553B",
}


# ── Chart 6: Sector Heatmap ──────────────────────────────────────────────────

def sector_heatmap(returns_by_period: dict) -> go.Figure:
    """Sector ETF performance heatmap: tickers x time periods."""
    periods = list(returns_by_period.keys())
    tickers = returns_by_period[periods[0]].index.tolist()
    z = []
    for ticker in tickers:
        row = [returns_by_period[p].get(ticker, 0) for p in periods]
        z.append(row)

    fig = go.Figure(go.Heatmap(
        z=z, x=periods, y=tickers,
        colorscale="RdYlGn", zmid=0,
        text=[[f"{v:.1f}%" for v in row] for row in z],
        texttemplate="%{text}",
        textfont={"size": 12},
        hovertemplate="Ticker: %{y}<br>Period: %{x}<br>Return: %{z:.2f}%<extra></extra>",
    ))
    fig.update_layout(
        title="Sector & Index ETF Returns",
        template=TEMPLATE, height=600,
        yaxis=dict(autorange="reversed"),
        margin=dict(t=60, b=40, l=60),
    )
    return fig


# ── Chart 7: Sector Bar Chart ────────────────────────────────────────────────

def sector_bar_chart(returns: pd.Series, period_label: str) -> go.Figure:
    """Horizontal bar chart. Benchmarks in gold."""
    colors = [
        "#FECB52" if t in BENCHMARKS
        else ("#00CC96" if v >= 0 else "#EF553B")
        for t, v in zip(returns.index, returns.values)
    ]
    fig = go.Figure(go.Bar(
        x=returns.values, y=returns.index,
        orientation="h", marker_color=colors,
        text=[f"{v:+.1f}%" for v in returns.values],
        textposition="outside",
    ))
    fig.update_layout(
        title=f"Sector Returns ({period_label})",
        template=TEMPLATE, height=600,
        xaxis_title="Return (%)",
        yaxis=dict(autorange="reversed"),
        margin=dict(t=60, b=40, r=80),
    )
    return fig


# ── Chart 8: Risk-Return Scatter ────────────────────────────────────────────

def risk_return_chart(rr: 'pd.DataFrame') -> go.Figure:
    """Scatter plot: annualized return vs volatility, sized by Sharpe ratio."""
    fig = go.Figure()

    for ticker in rr.index:
        ret = rr.loc[ticker, "Return (%)"]
        vol = rr.loc[ticker, "Volatility (%)"]
        sharpe = rr.loc[ticker, "Sharpe Ratio"]
        color = ETF_COLORS.get(ticker, "#888")
        is_bench = ticker in BENCHMARKS

        fig.add_trace(go.Scatter(
            x=[vol], y=[ret],
            mode="markers+text",
            name=ticker,
            text=[ticker],
            textposition="top center",
            textfont=dict(size=11, color="white"),
            marker=dict(
                size=18 if is_bench else 13,
                color=color,
                line=dict(width=2, color="white") if is_bench else dict(width=0),
                opacity=1 if is_bench else 0.7,
            ),
            hovertemplate=(
                f"<b>{ticker}</b><br>"
                f"Return: {ret:.1f}%<br>"
                f"Volatility: {vol:.1f}%<br>"
                f"Sharpe: {sharpe:.2f}<extra></extra>"
            ),
            showlegend=False,
        ))

    fig.update_layout(
        title="Risk vs. Return — Up-Left Is Best (High Return, Low Risk)",
        xaxis_title="Annualized Volatility (%)",
        yaxis_title="Annualized Return (%)",
        template=TEMPLATE, height=500,
        margin=dict(t=60, b=40),
    )
    return fig
