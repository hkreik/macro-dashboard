"""
app.py — Beginner learning dashboard entry point.

Layout order (top to bottom):
  1. Header
  2. "What is this dashboard?" intro
  3. Key indicators (KPI cards)
  4. Recession risk
  5. What's happening right now (briefing)
  6. Charts: S&P 500, Fear index, Fed vs Inflation, Yield Curve
  7. Sector performance (dropdown to change period)
  8. News
  9. Footer
"""

import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from flask_caching import Cache

from data import (
    get_all_fred_data, get_sector_data,
    compute_yield_spread, compute_sector_returns,
    compute_recession_score, get_market_news,
)
from charts import (
    sp500_sma_chart, fed_policy_chart, stress_chart,
    yield_curve_chart, sector_bar_chart,
)
from layouts import (
    build_header, build_footer, section_header,
    build_kpi_row, build_recession_panel,
    build_market_briefing, build_news_panel,
    C, SECTOR_NAMES,
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; }

body {
    background-color: #111827 !important;
    font-family: Inter, system-ui, sans-serif !important;
    color: #F9FAFB !important;
    margin: 0;
}

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #111827; }
::-webkit-scrollbar-thumb { background: #374151; border-radius: 3px; }

.card, .card-body { background: transparent !important; border: none !important; padding: 0 !important; }

/* Accordion styling */
.accordion-button { font-size: 12px !important; padding: 6px 0 !important; }
.accordion-button:not(.collapsed) { box-shadow: none !important; }
.accordion-body { padding: 8px 0 !important; }

/* News hover */
a { color: #60A5FA !important; }
a:hover { color: #93C5FD !important; }

.intro-box {
    background: #1F2937;
    border: 1px solid #374151;
    border-left: 4px solid #60A5FA;
    border-radius: 8px;
    padding: 18px 22px;
    margin-bottom: 28px;
}

.section-spacer { height: 28px; }
"""

# ── App init ─────────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}],
    suppress_callback_exceptions=True,
)
app.title = 'Stock Market Learning Dashboard'
server = app.server

app.index_string = f'''<!DOCTYPE html>
<html>
<head>
    {{%metas%}}
    <title>{{%title%}}</title>
    {{%favicon%}}
    {{%css%}}
    <style>{CSS}</style>
</head>
<body>
    {{%app_entry%}}
    <footer>{{%config%}}{{%scripts%}}{{%renderer%}}</footer>
</body>
</html>'''

# ── Cache ─────────────────────────────────────────────────────────────────────
cache = Cache(server, config={
    'CACHE_TYPE': 'FileSystemCache',
    'CACHE_DIR': 'cache-directory',
    'CACHE_DEFAULT_TIMEOUT': 3600,
})


@cache.memoize(timeout=3600)
def load_fred():
    return get_all_fred_data()


@cache.memoize(timeout=3600)
def load_sectors():
    return get_sector_data()


# ── Period options for sector chart ──────────────────────────────────────────
PERIODS = ['YTD', '1M', '3M', '6M', '1Y']

# ── Layout ────────────────────────────────────────────────────────────────────
app.layout = html.Div([
    build_header(),

    dbc.Container([

        # Intro explainer
        html.Div(style={'height': '24px'}),
        html.Div([
            html.H5('How to use this dashboard', style={
                'color': '#F9FAFB', 'fontWeight': '700', 'marginBottom': '10px',
            }),
            html.P([
                'This dashboard shows you the real economic forces that move stock prices — updated hourly. ',
                'Every number has a plain-English explanation below it. ',
                'Click the ',
                html.Strong('"What does this mean?"'),
                ' buttons under each section to learn why each metric matters.',
            ], style={'color': '#9CA3AF', 'fontSize': '13px', 'lineHeight': '1.8', 'margin': '0'}),
        ], className='intro-box'),

        # ── Key Indicators ───────────────────────────────────────────────────
        section_header(
            '📊  Key Market Indicators',
            explainer=(
                'These are the most important numbers watched by professional investors every day. '
                'Together they tell you: Is the economy growing or shrinking? Are investors nervous or calm? '
                'Is borrowing cheap or expensive? Each card shows the current number AND what it means right now.'
            )
        ),
        html.Div(id='kpi-row'),

        html.Div(style={'height': '32px'}),

        # ── Recession Risk ───────────────────────────────────────────────────
        section_header(
            '🚦  Recession Risk Score',
            explainer=(
                'A recession is when the economy shrinks for two or more quarters in a row — businesses earn less, '
                'unemployment rises, and stock prices usually fall significantly. '
                'This score tracks 6 warning signals that economists watch. '
                'It is NOT a guarantee — it is a probability estimate based on historical patterns. '
                'The yield curve inversion signal alone has preceded every US recession since 1960.'
            )
        ),
        html.Div(id='recession-panel'),

        html.Div(style={'height': '32px'}),

        # ── What's happening now ─────────────────────────────────────────────
        section_header(
            '📰  What\'s Happening Right Now',
            explainer=(
                'This section translates the raw numbers into plain-English stories. '
                'Think of it as a quick brief on the main forces shaping the market today.'
            )
        ),
        html.Div(id='briefing-panel'),

        html.Div(style={'height': '32px'}),

        # ── S&P 500 chart ────────────────────────────────────────────────────
        section_header(
            '📈  Is the Stock Market Trending Up or Down?',
            explainer=(
                'The S&P 500 (tracked by the SPY ETF) contains 500 of the largest US companies. '
                'When you hear "the market is up today," this is what they\'re talking about. '
                'The dotted yellow line is the 200-day moving average — the long-term trend. '
                'When the price is above the yellow line, the market is in a long-term uptrend (bullish). '
                'When it falls below, it may signal a longer-term downturn (bearish).'
            )
        ),
        dcc.Graph(id='chart-spy', config={'displayModeBar': False}),

        html.Div(style={'height': '32px'}),

        # ── Fear index ───────────────────────────────────────────────────────
        section_header(
            '😰  How Scared Are Investors? (VIX Fear Index)',
            explainer=(
                'The VIX measures how much investors expect prices to swing in the next 30 days. '
                'It\'s calculated from options prices — when investors pay a lot to protect against losses, VIX rises. '
                'Below 15 = calm and complacent. '
                '15-25 = normal uncertainty. '
                '25-35 = elevated worry. '
                'Above 35 = panic (happened during COVID crash, 2008 crisis, etc.). '
                'Interestingly, high VIX often marks a market BOTTOM — extreme fear can be a buying opportunity for long-term investors.'
            )
        ),
        dcc.Graph(id='chart-vix', config={'displayModeBar': False}),

        html.Div(style={'height': '32px'}),

        # ── Fed & Inflation ──────────────────────────────────────────────────
        section_header(
            '🏦  The Fed vs Inflation — The Most Important Battle in Markets',
            explainer=(
                'The Federal Reserve (the Fed) controls interest rates to keep inflation around 2%. '
                'When inflation gets too high, the Fed raises rates to make borrowing expensive — '
                'this slows spending and hiring, which brings prices down. But higher rates also '
                'make stocks less attractive (bonds pay more) and slow economic growth. '
                'This is why investors watch every Fed meeting so closely. '
                'The red line = Fed\'s rate. The yellow line = actual inflation. '
                'When the red is above the yellow, "real" rates are positive (restrictive). '
                'The green dotted line = the Fed\'s 2% target.'
            )
        ),
        dcc.Graph(id='chart-fed', config={'displayModeBar': False}),

        html.Div(style={'height': '32px'}),

        # ── Yield Curve ──────────────────────────────────────────────────────
        section_header(
            '📉  The Yield Curve — Why Bonds Predict Recessions',
            explainer=(
                'Bonds are loans you give to the government. In return, the government pays you interest. '
                'Normally, loans that last longer (10 years) pay more interest than short-term loans (2 years) — '
                'because you\'re tying up money for longer. '
                'But sometimes short-term rates go HIGHER than long-term rates. This is called an "inversion." '
                'Why does it matter? Because it means investors are so worried about the near-term economy '
                'that they\'re fleeing to long-term bonds, driving those rates down. '
                'An inverted yield curve has preceded every US recession in the last 60 years. '
                'Red shading below zero = inverted (warning). Green above zero = healthy.'
            )
        ),
        dcc.Graph(id='chart-yield', config={'displayModeBar': False}),

        html.Div(style={'height': '32px'}),

        # ── Sectors ──────────────────────────────────────────────────────────
        section_header(
            '🏭  Sector Performance — Which Parts of the Economy Are Winning?',
            explainer=(
                'The stock market isn\'t one thing — it\'s made up of different sectors (industries). '
                'Technology, Healthcare, Energy, Banks — each sector responds differently to the economy. '
                'For example: when interest rates rise, banks do better (they earn more on loans) '
                'but tech stocks fall (their future profits are worth less today). '
                'Watching which sectors are leading vs lagging tells you a lot about where investors '
                'think the economy is headed.'
            )
        ),
        dbc.Row([
            dbc.Col(html.Div([
                html.Label('Show performance over:', style={
                    'color': '#9CA3AF', 'fontSize': '12px', 'marginBottom': '6px',
                    'display': 'block',
                }),
                dcc.Dropdown(
                    id='period-dropdown',
                    options=[{'label': p, 'value': p} for p in PERIODS],
                    value='YTD',
                    clearable=False,
                    style={
                        'width': '130px',
                        'fontSize': '13px',
                    },
                ),
            ]), width='auto'),
        ], className='mb-3'),
        dcc.Graph(id='chart-sectors', config={'displayModeBar': False}),

        html.Div(style={'height': '32px'}),

        # ── News ─────────────────────────────────────────────────────────────
        section_header(
            '📰  Market News',
            explainer=(
                'These are recent headlines that are moving markets. '
                'As you learn the concepts on this dashboard, you\'ll start to understand '
                'WHY these headlines move stocks — for example: "Fed raises rates" → '
                'bonds become more attractive → investors sell stocks → market falls.'
            )
        ),
        html.Div(id='news-panel'),

    ], fluid=True, className='px-3 px-md-4'),

    build_footer(),
    dcc.Interval(id='refresh', interval=3600 * 1000, n_intervals=0),

], style={'backgroundColor': '#111827', 'minHeight': '100vh'})


# ── Callbacks ─────────────────────────────────────────────────────────────────

@app.callback(
    Output('kpi-row',        'children'),
    Output('recession-panel','children'),
    Output('briefing-panel', 'children'),
    Output('chart-spy',      'figure'),
    Output('chart-vix',      'figure'),
    Output('chart-fed',      'figure'),
    Output('chart-yield',    'figure'),
    Output('news-panel',     'children'),
    Input('refresh', 'n_intervals'),
)
def refresh_all(_):
    fred    = load_fred()
    sectors = load_sectors()
    spread  = compute_yield_spread(fred)
    score   = compute_recession_score(fred)
    news    = get_market_news()

    from data import compute_sector_returns
    _rets = compute_sector_returns(sectors, 'YTD')
    spy_return = float(_rets['SPY']) if 'SPY' in _rets.index else 0.0

    return (
        build_kpi_row(fred, spread, spy_return),
        build_recession_panel(score),
        build_market_briefing(fred, spread, spy_return),
        sp500_sma_chart(sectors),
        stress_chart(fred),
        fed_policy_chart(fred),
        yield_curve_chart(fred),
        build_news_panel(news),
    )


@app.callback(
    Output('chart-sectors', 'figure'),
    Input('period-dropdown', 'value'),
)
def update_sectors(period):
    sectors = load_sectors()
    from data import compute_sector_returns
    returns = compute_sector_returns(sectors, period or 'YTD')
    return sector_bar_chart(returns, period or 'YTD')


if __name__ == '__main__':
    app.run(debug=True)
