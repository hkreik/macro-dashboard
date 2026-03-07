import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# ---------------------------------------------------------------------------
# Bloomberg-grade theme
# Dark background (#0a0e1a), 2px lines, gridlines, inline annotations
# ---------------------------------------------------------------------------

BG_COLOR    = "#0a0e1a"   # near-black navy
PAPER_COLOR = "#0a0e1a"
GRID_COLOR  = "rgba(255,255,255,0.08)"
ZERO_COLOR  = "rgba(255,255,255,0.25)"
FONT_COLOR  = "#e0e4ef"
FONT_FAMILY = "IBM Plex Mono, Courier New, monospace"
AXIS_COLOR  = "rgba(255,255,255,0.18)"
LINE_WIDTH  = 2           # Bloomberg standard
HEIGHT      = 440

# Colour palette
C_BLUE   = "#4c9be8"
C_YELLOW = "#f0b429"
C_RED    = "#e85454"
C_GREEN  = "#2dce89"
C_PURPLE = "#a78bfa"
C_ORANGE = "#f97316"


def _base_layout(**extra) -> dict:
    """Return a base layout dict with the Bloomberg dark theme applied."""
    layout = dict(
        paper_bgcolor=PAPER_COLOR,
        plot_bgcolor=BG_COLOR,
        font=dict(color=FONT_COLOR, family=FONT_FAMILY, size=11),
        height=HEIGHT,
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#1a2035",
            bordercolor=GRID_COLOR,
            font=dict(color=FONT_COLOR, family=FONT_FAMILY, size=11),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=10),
        ),
        margin=dict(t=70, b=50, l=60, r=40),
        xaxis=dict(
            showgrid=True,
            gridcolor=GRID_COLOR,
            gridwidth=1,
            zeroline=False,
            linecolor=AXIS_COLOR,
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=GRID_COLOR,
            gridwidth=1,
            zeroline=False,
            linecolor=AXIS_COLOR,
            tickfont=dict(size=10),
        ),
    )
    layout.update(extra)
    return layout


def _title(text: str) -> dict:
    return dict(
        text=text,
        font=dict(size=13, color=FONT_COLOR, family=FONT_FAMILY),
        x=0,
        xanchor="left",
    )


def _inline_annotation(x, y, text, ax=0, ay=-28, color=FONT_COLOR) -> dict:
    """Small callout label pinned to a data point."""
    return dict(
        x=x, y=y,
        xref="x", yref="y",
        text=text,
        showarrow=True,
        arrowhead=0,
        arrowwidth=1,
        arrowcolor=color,
        ax=ax, ay=ay,
        font=dict(size=9, color=color, family=FONT_FAMILY),
        bgcolor="rgba(10,14,26,0.75)",
        bordercolor=color,
        borderwidth=1,
        borderpad=3,
    )


# ---------------------------------------------------------------------------
# Chart 1: S&P 500 with 50 / 200-day SMA
# ---------------------------------------------------------------------------

def sp500_sma_chart(spy_prices: pd.Series) -> go.Figure:
    spy    = spy_prices.dropna()
    sma50  = spy.rolling(50).mean()
    sma200 = spy.rolling(200).mean()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=spy.index, y=spy.values,
        name="SPY",
        line=dict(color=C_BLUE, width=LINE_WIDTH),
        hovertemplate="SPY: $%{y:,.2f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=sma50.index, y=sma50.values,
        name="50-Day SMA",
        line=dict(color=C_YELLOW, width=LINE_WIDTH, dash="dot"),
        hovertemplate="50d SMA: $%{y:,.2f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=sma200.index, y=sma200.values,
        name="200-Day SMA",
        line=dict(color=C_RED, width=LINE_WIDTH, dash="dot"),
        hovertemplate="200d SMA: $%{y:,.2f}<extra></extra>",
    ))

    # Inline annotations: label the most-recent value of each series
    annotations = []
    for series, label, color in [
        (spy,    "SPY",  C_BLUE),
        (sma50,  "50d",  C_YELLOW),
        (sma200, "200d", C_RED),
    ]:
        s = series.dropna()
        if len(s):
            annotations.append(_inline_annotation(
                x=s.index[-1], y=s.iloc[-1],
                text=f"{label} ${s.iloc[-1]:,.0f}",
                ax=36, ay=0, color=color,
            ))

    layout = _base_layout(
        title=_title("Is the Market Trending Up or Down?"),
        yaxis=dict(
            title="Price ($)",
            showgrid=True, gridcolor=GRID_COLOR, gridwidth=1,
            zeroline=False, linecolor=AXIS_COLOR, tickfont=dict(size=10),
            tickprefix="$",
        ),
        annotations=annotations,
    )
    fig.update_layout(layout)
    return fig


# ---------------------------------------------------------------------------
# Chart 2: System Stress -- VIX + High-Yield Credit Spread
# ---------------------------------------------------------------------------

def stress_chart(vix: pd.Series, hy_spread: pd.Series) -> go.Figure:
    vix = vix.dropna()
    hy  = hy_spread.dropna()

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=vix.index, y=vix.values,
            name="VIX (Fear Index)",
            line=dict(color=C_PURPLE, width=LINE_WIDTH),
            fill="tozeroy",
            fillcolor="rgba(167,139,250,0.08)",
            hovertemplate="VIX: %{y:.1f}<extra></extra>",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=hy.index, y=hy.values,
            name="HY Credit Spread (%)",
            line=dict(color=C_RED, width=LINE_WIDTH),
            hovertemplate="HY Spread: %{y:.2f}%%<extra></extra>",
        ),
        secondary_y=True,
    )

    # Panic-zone shading
    fig.add_hrect(
        y0=30, y1=max(vix.max() * 1.15, 60),
        fillcolor=C_RED, opacity=0.06,
        line_width=0,
        secondary_y=False,
    )

    # Inline annotations: latest values + panic-zone label
    annotations = []
    if len(vix):
        annotations.append(dict(
            x=vix.index[-1], y=vix.iloc[-1],
            xref="x", yref="y",
            text=f"VIX {vix.iloc[-1]:.1f}",
            showarrow=True, arrowhead=0, arrowwidth=1,
            arrowcolor=C_PURPLE, ax=36, ay=0,
            font=dict(size=9, color=C_PURPLE, family=FONT_FAMILY),
            bgcolor="rgba(10,14,26,0.75)",
            bordercolor=C_PURPLE, borderwidth=1, borderpad=3,
        ))
    if len(hy):
        annotations.append(dict(
            x=hy.index[-1], y=hy.iloc[-1],
            xref="x", yref="y2",
            text=f"HY {hy.iloc[-1]:.2f}%",
            showarrow=True, arrowhead=0, arrowwidth=1,
            arrowcolor=C_RED, ax=36, ay=0,
            font=dict(size=9, color=C_RED, family=FONT_FAMILY),
            bgcolor="rgba(10,14,26,0.75)",
            bordercolor=C_RED, borderwidth=1, borderpad=3,
        ))
    annotations.append(dict(
        x=vix.index[int(len(vix) * 0.05)], y=32,
        xref="x", yref="y",
        text="Panic Zone (VIX > 30)",
        showarrow=False,
        font=dict(size=9, color=C_RED, family=FONT_FAMILY),
        bgcolor="rgba(10,14,26,0)",
    ))

    layout = _base_layout(
        title=_title("How Much Stress Is in the System?"),
        annotations=annotations,
    )
    fig.update_layout(layout)
    fig.update_yaxes(
        title_text="VIX Level",
        showgrid=True, gridcolor=GRID_COLOR, gridwidth=1,
        linecolor=AXIS_COLOR, tickfont=dict(size=10),
        secondary_y=False,
    )
    fig.update_yaxes(
        title_text="Credit Spread (%)",
        showgrid=False,
        linecolor=AXIS_COLOR, tickfont=dict(size=10),
        secondary_y=True,
    )
    fig.update_xaxes(
        showgrid=True, gridcolor=GRID_COLOR, gridwidth=1,
        linecolor=AXIS_COLOR, tickfont=dict(size=10),
    )
    fig.update_layout(paper_bgcolor=PAPER_COLOR, plot_bgcolor=BG_COLOR)
    return fig


# ---------------------------------------------------------------------------
# Chart 3: Fed Policy -- CPI Inflation vs Fed Funds Rate
# ---------------------------------------------------------------------------

def fed_policy_chart(df: pd.DataFrame) -> go.Figure:
    inflation = df["CPI Inflation (Trimmed Mean)"].dropna()
    fed_rate  = df["Federal Funds Rate"].dropna()

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=inflation.index, y=inflation.values,
            name="CPI Inflation (Trimmed Mean, %)",
            line=dict(color=C_ORANGE, width=LINE_WIDTH),
            fill="tozeroy",
            fillcolor="rgba(249,115,22,0.08)",
            hovertemplate="CPI: %{y:.2f}%%<extra></extra>",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=fed_rate.index, y=fed_rate.values,
            name="Fed Funds Rate (%)",
            line=dict(color=C_GREEN, width=LINE_WIDTH),
            hovertemplate="Fed Rate: %{y:.2f}%%<extra></extra>",
        ),
        secondary_y=True,
    )

    # Fed target zone shading
    fig.add_hrect(
        y0=0, y1=2.5,
        fillcolor=C_GREEN, opacity=0.06,
        line_width=0,
        secondary_y=False,
    )

    # Inline annotations
    annotations = []
    if len(inflation):
        annotations.append(dict(
            x=inflation.index[-1], y=inflation.iloc[-1],
            xref="x", yref="y",
            text=f"CPI {inflation.iloc[-1]:.1f}%",
            showarrow=True, arrowhead=0, arrowwidth=1,
            arrowcolor=C_ORANGE, ax=38, ay=0,
            font=dict(size=9, color=C_ORANGE, family=FONT_FAMILY),
            bgcolor="rgba(10,14,26,0.75)",
            bordercolor=C_ORANGE, borderwidth=1, borderpad=3,
        ))
    if len(fed_rate):
        annotations.append(dict(
            x=fed_rate.index[-1], y=fed_rate.iloc[-1],
            xref="x", yref="y2",
            text=f"Fed {fed_rate.iloc[-1]:.2f}%",
            showarrow=True, arrowhead=0, arrowwidth=1,
            arrowcolor=C_GREEN, ax=38, ay=0,
            font=dict(size=9, color=C_GREEN, family=FONT_FAMILY),
            bgcolor="rgba(10,14,26,0.75)",
            bordercolor=C_GREEN, borderwidth=1, borderpad=3,
        ))
    annotations.append(dict(
        x=inflation.index[int(len(inflation) * 0.05)], y=1.25,
        xref="x", yref="y",
        text="Fed Target Zone (0-2.5%)",
        showarrow=False,
        font=dict(size=9, color=C_GREEN, family=FONT_FAMILY),
        bgcolor="rgba(10,14,26,0)",
    ))

    layout = _base_layout(
        title=_title("Is the Fed Winning the Inflation Fight?"),
        annotations=annotations,
    )
    fig.update_layout(layout)
    fig.update_yaxes(
        title_text="Inflation (%)",
        showgrid=True, gridcolor=GRID_COLOR, gridwidth=1,
        linecolor=AXIS_COLOR, tickfont=dict(size=10),
        secondary_y=False,
    )
    fig.update_yaxes(
        title_text="Fed Funds Rate (%)",
        showgrid=False,
        linecolor=AXIS_COLOR, tickfont=dict(size=10),
        secondary_y=True,
    )
    fig.update_xaxes(
        showgrid=True, gridcolor=GRID_COLOR, gridwidth=1,
        linecolor=AXIS_COLOR, tickfont=dict(size=10),
    )
    fig.update_layout(paper_bgcolor=PAPER_COLOR, plot_bgcolor=BG_COLOR)
    return fig


# ---------------------------------------------------------------------------
# Chart 4: Macro-Equity Correlations (horizontal bar)
# ---------------------------------------------------------------------------

def correlation_chart(corr_df: pd.DataFrame) -> go.Figure:
    df     = corr_df.sort_values("correlation")
    colors = [C_RED if v < 0 else C_GREEN for v in df["correlation"]]

    annotations = []
    for indicator, corr in zip(df["indicator"], df["correlation"]):
        annotations.append(dict(
            x=corr + (0.04 if corr >= 0 else -0.04),
            y=indicator,
            xref="x", yref="y",
            text=f"{corr:+.2f}",
            showarrow=False,
            xanchor="left" if corr >= 0 else "right",
            font=dict(
                size=10,
                color=C_GREEN if corr >= 0 else C_RED,
                family=FONT_FAMILY,
            ),
        ))

    fig = go.Figure(go.Bar(
        x=df["correlation"],
        y=df["indicator"],
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=None,
        hovertemplate="%{y}: %{x:+.2f}<extra></extra>",
    ))

    layout = _base_layout(
        title=_title("What Drives the S&P 500? (Macro Correlations)"),
        xaxis=dict(
            title="Pearson Correlation with SPY Monthly Return",
            range=[-1.15, 1.15],
            zeroline=True,
            zerolinecolor=ZERO_COLOR,
            zerolinewidth=1,
            showgrid=True, gridcolor=GRID_COLOR, gridwidth=1,
            linecolor=AXIS_COLOR, tickfont=dict(size=10),
        ),
        yaxis=dict(
            showgrid=False,
            linecolor=AXIS_COLOR, tickfont=dict(size=10),
        ),
        margin=dict(t=70, b=50, l=200, r=60),
        annotations=annotations,
        bargap=0.35,
    )
    fig.update_layout(layout)
    return fig


# ---------------------------------------------------------------------------
# Chart 5: Sector & Index Returns (bar chart)
# ---------------------------------------------------------------------------

def sector_bar_chart(returns: pd.Series, period: str = "YTD") -> go.Figure:
    colors = [C_GREEN if v >= 0 else C_RED for v in returns.values]

    annotations = []
    for ticker, val in zip(returns.index, returns.values):
        annotations.append(dict(
            x=ticker,
            y=val + (0.4 if val >= 0 else -0.4),
            xref="x", yref="y",
            text=f"{val:+.1f}%",
            showarrow=False,
            yanchor="bottom" if val >= 0 else "top",
            font=dict(
                size=9,
                color=C_GREEN if val >= 0 else C_RED,
                family=FONT_FAMILY,
            ),
        ))

    fig = go.Figure(go.Bar(
        x=returns.index,
        y=returns.values,
        marker=dict(color=colors, line=dict(width=0)),
        text=None,
        hovertemplate="%{x}: %{y:+.1f}%<extra></extra>",
    ))

    layout = _base_layout(
        title=_title(f"Sector & Index Returns ({period})"),
        yaxis=dict(
            title="Return (%)",
            showgrid=True, gridcolor=GRID_COLOR, gridwidth=1,
            zeroline=True, zerolinecolor=ZERO_COLOR, zerolinewidth=1,
            linecolor=AXIS_COLOR, tickfont=dict(size=10),
            ticksuffix="%",
        ),
        xaxis=dict(
            showgrid=False,
            linecolor=AXIS_COLOR, tickfont=dict(size=10),
        ),
        annotations=annotations,
        bargap=0.3,
    )
    fig.update_layout(layout)
    return fig
