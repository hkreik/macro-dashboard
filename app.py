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
from charts import (
    sp500_sma_chart, stress_chart, fed_policy_chart,
    sector_bar_chart, correlation_chart,
)
from layouts import (
    make_kpi_card, build_kpi_row, build_recession_panel,
    build_market_briefing, build_news_panel,
)

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
app.title = "Macro-Equity Dashboard"
server = app.server

cache = Cache(server, config={
    "CACHE_TYPE": "FileSystemCache",
    "CACHE_DIR": "cache-directory",
    "CACHE_DEFAULT_TIMEOUT": 3600,
})


@cache.memoize(timeout=3600)
def load_fred():
    return get_all_fred_data()


@cache.memoize(timeout=3600)
def load_sectors():
    return get_sector_data()


# -- Layout ----------------------------------------------------------------------

app.layout = dbc.Container([
    dbc.Row(dbc.Col(html.H2("Macro-Equity Dashboard",
                             className="text-center my-4",
                             style={"letterSpacing": "0.05em"}), width=12)),

    html.Div(id="kpi-row"),
    html.Div(id="recession-panel"),
    html.Div(id="briefing-panel"),
    html.Div(id="news-panel"),

    dbc.Row([
        dbc.Col(dcc.Graph(id="chart-sp500"), md=6),
        dbc.Col(dcc.Graph(id="chart-stress"), md=6),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(dcc.Graph(id="chart-fed"), md=6),
        dbc.Col(dcc.Graph(id="chart-correlation"), md=6),
    ], className="mb-4"),

    dbc.Row(dbc.Col([
        html.P("Sector Performance", className="text-muted mb-2"),
        dbc.ButtonGroup([
            dbc.Button("YTD", id="btn-ytd", n_clicks=0, size="sm", color="primary", outline=True),
            dbc.Button("1M",  id="btn-1m",  n_clicks=0, size="sm", color="secondary", outline=True),
            dbc.Button("3M",  id="btn-3m",  n_clicks=0, size="sm", color="secondary", outline=True),
            dbc.Button("6M",  id="btn-6m",  n_clicks=0, size="sm", color="secondary", outline=True),
            dbc.Button("1Y",  id="btn-1y",  n_clicks=0, size="sm", color="secondary", outline=True),
        ], className="mb-3"),
    ], width=12)),

    dbc.Row(dbc.Col(dcc.Graph(id="chart-sectors"), width=12), className="mb-4"),

    dbc.Row(dbc.Col(
        html.P("Data refreshes every hour. Sources: FRED (Federal Reserve), Yahoo Finance.",
               className="text-muted text-center", style={"fontSize": "0.75rem"}),
        width=12
    )),

    dcc.Interval(id="interval", interval=3600 * 1000, n_intervals=0),
], fluid=True, className="px-4")


# -- Callbacks -------------------------------------------------------------------

@app.callback(
    Output("kpi-row", "children"),
    Output("recession-panel", "children"),
    Output("briefing-panel", "children"),
    Output("news-panel", "children"),
    Output("chart-sp500", "figure"),
    Output("chart-stress", "figure"),
    Output("chart-fed", "figure"),
    Output("chart-correlation", "figure"),
    Input("interval", "n_intervals"),
)
def update_main(n):
    df = load_fred()
    prices = load_sectors()
    spread = compute_yield_spread(df)

    spy_prices = prices["SPY"]
    ytd_start = spy_prices[spy_prices.index.year == spy_prices.index[-1].year].iloc[0]
    spy_return = ((spy_prices.iloc[-1] - ytd_start) / ytd_start) * 100

    corr_df = compute_macro_correlations(df, prices)
    recession_data = compute_recession_score(df, prices)
    news_items = get_market_news()

    return (
        build_kpi_row(df, spread, spy_return),
        build_recession_panel(recession_data),
        build_market_briefing(df, spread, spy_return, recession_data),
        build_news_panel(news_items),
        sp500_sma_chart(spy_prices),
        stress_chart(df["VIX"], df["High Yield Spread"]),
        fed_policy_chart(df),
        correlation_chart(corr_df),
    )


@app.callback(
    Output("chart-sectors", "figure"),
    Output("btn-ytd", "color"), Output("btn-ytd", "outline"),
    Output("btn-1m",  "color"), Output("btn-1m",  "outline"),
    Output("btn-3m",  "color"), Output("btn-3m",  "outline"),
    Output("btn-6m",  "color"), Output("btn-6m",  "outline"),
    Output("btn-1y",  "color"), Output("btn-1y",  "outline"),
    Input("btn-ytd", "n_clicks"),
    Input("btn-1m",  "n_clicks"),
    Input("btn-3m",  "n_clicks"),
    Input("btn-6m",  "n_clicks"),
    Input("btn-1y",  "n_clicks"),
)
def update_sector_chart(n_ytd, n_1m, n_3m, n_6m, n_1y):
    from dash import ctx
    triggered = ctx.triggered_id or "btn-ytd"
    period_map = {
        "btn-ytd": "YTD", "btn-1m": "1M",
        "btn-3m": "3M",   "btn-6m": "6M", "btn-1y": "1Y",
    }
    period = period_map.get(triggered, "YTD")
    prices = load_sectors()
    returns = compute_sector_returns(prices, period)

    buttons = ["btn-ytd", "btn-1m", "btn-3m", "btn-6m", "btn-1y"]
    result = [sector_bar_chart(returns, period)]
    for btn in buttons:
        if btn == triggered:
            result += ["primary", False]
        else:
            result += ["secondary", True]
    return result


if __name__ == "__main__":
    app.run(debug=True)
