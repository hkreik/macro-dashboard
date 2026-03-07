"""
charts.py — Beginner-friendly chart builders.

Design principles:
- Soft dark theme (not pitch black)
- Every line is labeled directly on the chart
- Plain-English annotations explain what you're looking at
- Fewer visual elements — cleaner and easier to read
- Color = meaning: green good, red bad, blue neutral
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# ── Theme ────────────────────────────────────────────────────────────────────
BG      = '#111827'
SURFACE = '#1F2937'
GRID    = 'rgba(255,255,255,0.06)'
TEXT    = '#F9FAFB'
SUBTEXT = '#9CA3AF'
FONT    = 'Inter, system-ui, sans-serif'

BLUE   = '#60A5FA'
GREEN  = '#34D399'
RED    = '#F87171'
AMBER  = '#FBBF24'
PURPLE = '#A78BFA'

HEIGHT = 380

SECTOR_COLORS = {
    'XLK':  '#60A5FA',  # blue  — Technology
    'XLF':  '#34D399',  # green — Finance
    'XLE':  '#FBBF24',  # amber — Energy
    'XLV':  '#A78BFA',  # purple — Healthcare
    'XLI':  '#F97316',  # orange — Industrials
    'XLC':  '#38BDF8',  # sky — Communication
    'XLY':  '#FB7185',  # pink — Consumer Disc.
    'XLP':  '#86EFAC',  # light green — Consumer Staples
    'XLU':  '#FDE68A',  # yellow — Utilities
    'XLRE': '#C084FC',  # violet — Real Estate
    'XLB':  '#6EE7B7',  # teal — Materials
    'SPY':  '#60A5FA',
    'QQQ':  '#818CF8',
    'DIA':  '#34D399',
    'IWM':  '#FBBF24',
}

SECTOR_NAMES = {
    'XLK':  'Technology',
    'XLF':  'Finance & Banks',
    'XLE':  'Energy & Oil',
    'XLV':  'Healthcare',
    'XLI':  'Industrials',
    'XLC':  'Communication',
    'XLY':  'Consumer (Discretionary)',
    'XLP':  'Consumer (Staples)',
    'XLU':  'Utilities',
    'XLRE': 'Real Estate',
    'XLB':  'Materials',
    'SPY':  'S&P 500',
    'QQQ':  'Nasdaq 100',
    'DIA':  'Dow Jones',
    'IWM':  'Small Caps',
}


def _base(title: str, height: int = HEIGHT) -> dict:
    return dict(
        paper_bgcolor=BG,
        plot_bgcolor=SURFACE,
        height=height,
        font=dict(family=FONT, color=TEXT, size=12),
        title=dict(text=title, font=dict(size=13, color=TEXT), x=0, xanchor='left'),
        hovermode='x unified',
        hoverlabel=dict(bgcolor='#1F2937', font=dict(color=TEXT, size=12)),
        legend=dict(
            orientation='h', y=1.08, x=0,
            bgcolor='rgba(0,0,0,0)', font=dict(size=11),
        ),
        margin=dict(t=60, b=50, l=55, r=30),
        xaxis=dict(
            showgrid=False, zeroline=False,
            linecolor='rgba(255,255,255,0.1)',
            tickfont=dict(size=10, color=SUBTEXT),
        ),
        yaxis=dict(
            showgrid=True, gridcolor=GRID, gridwidth=1,
            zeroline=False, linecolor='rgba(255,255,255,0.1)',
            tickfont=dict(size=10, color=SUBTEXT),
        ),
    )


def _annotation(x, y, text, color=SUBTEXT, ay=-30) -> dict:
    return dict(
        x=x, y=y, xref='x', yref='y',
        text=text, showarrow=True,
        arrowhead=0, arrowwidth=1, arrowcolor=color,
        ax=0, ay=ay,
        font=dict(size=10, color=color, family=FONT),
        bgcolor='rgba(31,41,55,0.85)',
        bordercolor=color, borderwidth=1, borderpad=4,
    )


# ── Chart 1: S&P 500 with 200-day moving average ────────────────────────────

def sp500_sma_chart(prices: pd.DataFrame) -> go.Figure:
    """
    Shows the S&P 500 (SPY ETF) price and its 200-day average.
    The 200-day average is a widely-watched trend line:
    - Price above it = long-term uptrend (bullish)
    - Price below it = long-term downtrend (bearish)
    """
    if 'SPY' not in prices.columns:
        return go.Figure()

    spy = prices['SPY'].dropna().tail(504)  # ~2 years
    sma200 = spy.rolling(200).mean()

    last_price = spy.iloc[-1]
    last_date  = spy.index[-1]
    above = last_price > sma200.iloc[-1]

    fig = go.Figure()

    # Price area fill
    fig.add_trace(go.Scatter(
        x=spy.index, y=spy,
        name='S&P 500 (SPY)',
        line=dict(color=BLUE, width=2),
        fill='tozeroy',
        fillcolor='rgba(96,165,250,0.06)',
        hovertemplate='$%{y:.2f}',
    ))

    # 200-day SMA
    fig.add_trace(go.Scatter(
        x=sma200.index, y=sma200,
        name='200-day average',
        line=dict(color=AMBER, width=1.5, dash='dot'),
        hovertemplate='Avg: $%{y:.2f}',
    ))

    annotations = [_annotation(
        last_date, last_price,
        f'Today: ${last_price:.0f}<br>{"↑ Above 200-day avg" if above else "↓ Below 200-day avg"}',
        color=GREEN if above else RED, ay=-40,
    )]

    fig.update_layout(
        **_base('S&P 500 — Is the market trending up or down?'),
        annotations=annotations,
        yaxis=dict(
            tickprefix='$', showgrid=True, gridcolor=GRID,
            zeroline=False, tickfont=dict(size=10, color=SUBTEXT),
        ),
    )
    return fig


# ── Chart 2: Fed Rate vs Inflation ───────────────────────────────────────────

def fed_policy_chart(fred_df: pd.DataFrame) -> go.Figure:
    """
    Shows the Fed interest rate vs inflation.
    When the Fed rate > inflation = 'real' positive rate, restrictive.
    When the Fed rate < inflation = money is still 'cheap' despite rate hikes.
    """
    fig = go.Figure()

    if 'Federal Funds Rate' in fred_df.columns:
        ffr = fred_df['Federal Funds Rate'].dropna().tail(252 * 5)
        fig.add_trace(go.Scatter(
            x=ffr.index, y=ffr,
            name='Fed Interest Rate',
            line=dict(color=RED, width=2),
            hovertemplate='Fed Rate: %{y:.2f}%',
        ))

    if 'CPI Inflation (Trimmed Mean)' in fred_df.columns:
        cpi = fred_df['CPI Inflation (Trimmed Mean)'].dropna().tail(252 * 5)
        fig.add_trace(go.Scatter(
            x=cpi.index, y=cpi,
            name='Inflation',
            line=dict(color=AMBER, width=2),
            hovertemplate='Inflation: %{y:.2f}%',
        ))

    if '10-Year Treasury' in fred_df.columns:
        t10 = fred_df['10-Year Treasury'].dropna().tail(252 * 5)
        fig.add_trace(go.Scatter(
            x=t10.index, y=t10,
            name='10-Year Bond Rate',
            line=dict(color=BLUE, width=1.5, dash='dot'),
            hovertemplate='10Y: %{y:.2f}%',
        ))

    # 2% target line
    fig.add_hline(
        y=2, line_dash='dash', line_color='rgba(52,211,153,0.4)', line_width=1,
        annotation_text="Fed's 2% inflation target",
        annotation_font=dict(size=10, color=GREEN),
        annotation_position='right',
    )

    fig.update_layout(
        **_base('Fed Rate vs Inflation — Is borrowing expensive right now?'),
        yaxis=dict(
            ticksuffix='%', showgrid=True, gridcolor=GRID,
            zeroline=False, tickfont=dict(size=10, color=SUBTEXT),
        ),
    )
    return fig


# ── Chart 3: Fear & Stress (VIX) ────────────────────────────────────────────

def stress_chart(fred_df: pd.DataFrame) -> go.Figure:
    """
    The VIX ('fear index') measures how much the market expects prices to swing.
    Low VIX = calm. High VIX = panic or uncertainty.
    Above 30 is historically associated with market crises.
    """
    fig = go.Figure()

    if 'VIX' not in fred_df.columns:
        return fig

    vix = fred_df['VIX'].dropna().tail(252 * 3)

    fig.add_trace(go.Scatter(
        x=vix.index, y=vix,
        name='VIX Fear Index',
        line=dict(color=RED, width=2),
        fill='tozeroy',
        fillcolor='rgba(248,113,113,0.08)',
        hovertemplate='VIX: %{y:.1f}',
    ))

    # Reference bands
    fig.add_hrect(y0=0,  y1=15,  fillcolor='rgba(52,211,153,0.05)', line_width=0, layer='below')
    fig.add_hrect(y0=15, y1=25,  fillcolor='rgba(251,191,36,0.04)', line_width=0, layer='below')
    fig.add_hrect(y0=25, y1=100, fillcolor='rgba(248,113,113,0.04)', line_width=0, layer='below')

    fig.add_hline(y=15, line_dash='dot', line_color='rgba(52,211,153,0.3)', line_width=1,
                  annotation_text='Calm (<15)', annotation_font=dict(size=9, color=GREEN),
                  annotation_position='right')
    fig.add_hline(y=25, line_dash='dot', line_color='rgba(251,191,36,0.4)', line_width=1,
                  annotation_text='Worry (>25)', annotation_font=dict(size=9, color=AMBER),
                  annotation_position='right')
    fig.add_hline(y=35, line_dash='dot', line_color='rgba(248,113,113,0.5)', line_width=1,
                  annotation_text='Panic (>35)', annotation_font=dict(size=9, color=RED),
                  annotation_position='right')

    fig.update_layout(
        **_base('VIX Fear Index — How scared are investors right now?'),
        yaxis=dict(
            showgrid=True, gridcolor=GRID, range=[0, max(vix.max() * 1.1, 40)],
            zeroline=False, tickfont=dict(size=10, color=SUBTEXT),
        ),
        showlegend=False,
    )
    return fig


# ── Chart 4: Yield Curve ─────────────────────────────────────────────────────

def yield_curve_chart(fred_df: pd.DataFrame) -> go.Figure:
    """
    The yield curve compares short-term vs long-term interest rates.
    Normally long-term rates are higher (positive spread).
    When short-term rates are HIGHER = 'inverted' = recession warning.
    """
    if '10-Year Treasury' not in fred_df.columns or '2-Year Treasury' not in fred_df.columns:
        return go.Figure()

    t10 = fred_df['10-Year Treasury'].dropna()
    t2  = fred_df['2-Year Treasury'].dropna()
    spread = (t10 - t2).dropna().tail(252 * 5)

    positive = spread.clip(lower=0)
    negative = spread.clip(upper=0)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=spread.index, y=spread,
        name='10Y minus 2Y rate',
        line=dict(color=BLUE, width=2),
        hovertemplate='Spread: %{y:.2f}%',
    ))

    fig.add_trace(go.Scatter(
        x=negative.index, y=negative,
        name='Inverted (warning zone)',
        fill='tozeroy',
        fillcolor='rgba(248,113,113,0.2)',
        line=dict(width=0),
        hoverinfo='skip',
    ))

    fig.add_trace(go.Scatter(
        x=positive.index, y=positive,
        name='Normal (healthy zone)',
        fill='tozeroy',
        fillcolor='rgba(52,211,153,0.1)',
        line=dict(width=0),
        hoverinfo='skip',
    ))

    fig.add_hline(y=0, line_color='rgba(255,255,255,0.3)', line_width=1,
                  annotation_text='Zero line — inversion starts here',
                  annotation_font=dict(size=9, color=SUBTEXT),
                  annotation_position='right')

    fig.update_layout(
        **_base('Yield Curve — Is a recession warning flashing?'),
        yaxis=dict(
            ticksuffix='%', showgrid=True, gridcolor=GRID,
            zeroline=False, tickfont=dict(size=10, color=SUBTEXT),
        ),
    )
    return fig


# ── Chart 5: Sector bar chart ────────────────────────────────────────────────

def sector_bar_chart(returns: pd.Series, period: str = 'YTD') -> go.Figure:
    """
    Shows how each sector of the economy is performing.
    Green = up, Red = down. Taller bars = bigger move.
    """
    if returns.empty:
        return go.Figure()

    # Use real sector names
    labels = [SECTOR_NAMES.get(t, t) for t in returns.index]
    colors = [SECTOR_COLORS.get(t, GREEN) if v >= 0 else RED
              for t, v in zip(returns.index, returns.values)]

    fig = go.Figure(go.Bar(
        x=labels,
        y=returns.values,
        marker_color=colors,
        marker_line_width=0,
        text=[f'{v:+.1f}%' for v in returns.values],
        textposition='outside',
        textfont=dict(size=10, color=TEXT),
        hovertemplate='%{x}<br>Return: %{y:.2f}%<extra></extra>',
    ))

    fig.add_hline(y=0, line_color='rgba(255,255,255,0.2)', line_width=1)

    fig.update_layout(
        **_base(f'Sector Performance ({period}) — Which parts of the economy are winning?', height=400),
        yaxis=dict(
            ticksuffix='%', showgrid=True, gridcolor=GRID,
            zeroline=False, tickfont=dict(size=10, color=SUBTEXT),
        ),
        bargap=0.3,
        showlegend=False,
        xaxis=dict(
            showgrid=False, tickangle=-30,
            tickfont=dict(size=10, color=SUBTEXT),
        ),
    )
    return fig
