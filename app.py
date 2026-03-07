import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
from flask_caching import Cache

from data import (
    get_all_fred_data, get_sector_data,
    compute_yield_spread, compute_sector_returns,
    compute_macro_correlations, compute_recession_score,
    get_market_news,
)
from charts import sp500_sma_chart, stress_chart, fed_policy_chart, sector_bar_chart, correlation_chart
from layouts import (
    build_header, build_footer, section_label,
    build_kpi_row, build_recession_panel,
    build_market_briefing, build_news_panel,
)

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; }

body {
    background-color: #0D1117 !important;
    font-family: Inter, system-ui, -apple-system, sans-serif !important;
    color: #E6EDF3 !important;
    margin: 0;
}

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0D1117; }
::-webkit-scrollbar-thumb { background: #21262D; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #484F58; }

.card { background: transparent !important; border: none !important; }
.card-body { padding: 0 !important; }

.news-row { transition: background-color 0.15s ease; border-radius: 4px; }
.news-row:hover { background-color: rgba(88,166,255,0.06); }
.news-row a:hover { color: #58A6FF !important; }

.pill-tab {
    background: transparent;
    border: 1px solid #21262D;
    color: #8B949E;
    border-radius: 20px;
    padding: 3px 14px;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s ease;
    margin-right: 6px;
    font-family: Inter, sans-serif;
}
.pill-tab:hover { border-color: #58A6FF; color: #E6EDF3; }
.pill-tab.active {
    background: rgba(88,166,255,0.15);
    border-color: #58A6FF;
    color: #58A6FF;
    font-weight: 600;
}

.dash-graph { border-radius: 6px; overflow: hidden; }
a { color: #58A6FF; }
a:hover { color: #79C0FF; }
"""

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}],
    suppress_callback_exceptions=True,
)
app.title = 'Macro-Equity Dashboard'
server = app.server

app.index_string = f'''<!DOCTYPE html>
<html>
<head>
    {{%metas%}}
    <title>{{%title%}}</title>
    {{%favicon%}}
    {{%css%}}
    <style>{CUSTOM_CSS}</style>
</head>
<body>
    {{%app_entry%}}
    <footer>{{%config%}}{{%scripts%}}{{%renderer%}}</footer>
</body>
</html>'''

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


PERIOD_OPTIONS = ['YTD', '1M', '3M', '6M', '1Y']

app.layout = html.Div([
    build_header(),
    dbc.Container([
        html.Div(style={'height': '28px'}),
        section_label('Key Indicators', 'Real-time macro snapshot'),
        html.Div(id='kpi-row'),

        html.Div(style={'height': '24px'}),
        section_label('Recession Risk Monitor'),
        html.Div(id='recession-panel'),

        html.Div(style={'height': '24px'}),
        section_label('Macro Regime', 'Current environment at a glance'),
        html.Div(id='briefing-panel'),

        html.Div(style={'height': '24px'}),
        section_label('Equity & Stress'),
        dbc.Row([
            dbc.Col(dcc.Graph(id='chart-sp500',  config={'displayModeBar': False}), md=6, className='mb-4'),
            dbc.Col(dcc.Graph(id='chart-stress', config={'displayModeBar': False}), md=6, className='mb-4'),
        ]),

        section_label('Policy & Correlations'),
        dbc.Row([
            dbc.Col(dcc.Graph(id='chart-fed',        config={'displayModeBar': False}), md=6, className='mb-4'),
            dbc.Col(dcc.Graph(id='chart-correlation', config={'displayModeBar': False}), md=6, className='mb-4'),
        ]),

        section_label('Sector Performance', 'Click a period to update'),
        html.Div([
            html.Button(p, id=f'pill-{p.lower()}',
                        className='pill-tab' + (' active' if p == 'YTD' else ''),
                        n_clicks=0)
            for p in PERIOD_OPTIONS
        ], style={'marginBottom': '16px'}),
        dbc.Row(dbc.Col(
            dcc.Graph(id='chart-sectors', config={'displayModeBar': False}),
            width=12
        ), className='mb-4'),

        section_label('Market News'),
        html.Div(id='news-panel'),

        build_footer(),
    ], fluid=True, className='px-3 px-md-4'),

    dcc.Interval(id='interval', interval=3600 * 1000, n_intervals=0),
], style={'backgroundColor': '#0D1117', 'minHeight': '100vh'})


@app.callback(
    Output('kpi-row',         'children'),
    Output('recession-panel', 'children'),
    Output('briefing-panel',  'children'),
    Output('news-panel',      'children'),
    Output('chart-sp500',     'figure'),
    Output('chart-stress',    'figure'),
    Output('chart-fed',       'figure'),
    Output('chart-correlation', 'figure'),
    Input('interval', 'n_intervals'),
)
def update_dashboard(n):
    df         = load_fred()
    sector_df  = load_sectors()
    spread     = compute_yield_spread(df)
    spy_prices = sector_df['SPY']
    spy_return = compute_sector_returns(sector_df, 'YTD')['SPY']
    recession  = compute_recession_score(df, spread)
    news       = get_market_news()
    return (
        build_kpi_row(df, spread, spy_return),
        build_recession_panel(recession),
        build_market_briefing(df, spread, spy_return),
        build_news_panel(news),
        sp500_sma_chart(spy_prices),
        stress_chart(df['VIX'], df['High Yield Spread']),
        fed_policy_chart(df),
        correlation_chart(compute_macro_correlations(df)),
    )


@app.callback(
    Output('chart-sectors', 'figure'),
    *[Output(f'pill-{p.lower()}', 'className') for p in PERIOD_OPTIONS],
    *[Input(f'pill-{p.lower()}', 'n_clicks') for p in PERIOD_OPTIONS],
)
def update_sectors(*args):
    ctx = dash.callback_context
    period = 'YTD'
    if ctx.triggered:
        btn_id = ctx.triggered[0]['prop_id'].split('.')[0]
        period = {f'pill-{p.lower()}': p for p in PERIOD_OPTIONS}.get(btn_id, 'YTD')
    sector_df = load_sectors()
    returns   = compute_sector_returns(sector_df, period)
    classes   = ['pill-tab active' if p == period else 'pill-tab' for p in PERIOD_OPTIONS]
    return sector_bar_chart(returns, period), *classes


if __name__ == '__main__':
    app.run(debug=True)
