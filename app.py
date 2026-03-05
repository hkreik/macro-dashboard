import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
from flask_caching import Cache

from data import (
    get_all_fred_data, get_sector_data,
    compute_yield_spread, compute_sector_returns, compute_risk_return,
)
from charts import (
    sp500_sma_chart, vix_chart, inflation_chart, yield_spread_chart,
    fed_unemployment_chart,
    sector_heatmap, sector_bar_chart, risk_return_chart,
)

# ── App init ──────────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
app.title = "Macro-Equity Dashboard"
server = app.server  # for gunicorn

# ── Cache (1-hour TTL, filesystem-based) ──────────────────────────────────────
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


# ── Helper: KPI cards ────────────────────────────────────────────────────────

def make_kpi_card(title, value, subtitle="", color="white"):
    return dbc.Col(dbc.Card(dbc.CardBody([
        html.P(title, className="text-muted mb-1", style={"fontSize": "0.8rem"}),
        html.H4(value, className="mb-0", style={"color": color}),
        html.Small(subtitle, className="text-muted") if subtitle else None,
    ]), className="bg-dark border-secondary"), md=2, sm=4, xs=6, className="mb-3")


def build_kpi_row(df, spread, spy_return):
    inflation = df["CPI Inflation (Trimmed Mean)"].dropna().iloc[-1]
    fed_rate = df["Federal Funds Rate"].dropna().iloc[-1]
    vix_val = df["VIX"].dropna().iloc[-1]
    spread_val = spread.dropna().iloc[-1]
    hy = df["High Yield Spread"].dropna().iloc[-1]

    spy_color = "#00CC96" if spy_return >= 0 else "#EF553B"
    vix_color = "#00CC96" if vix_val < 20 else ("#FECB52" if vix_val < 30 else "#EF553B")
    infl_color = "#00CC96" if inflation < 2.5 else ("#FECB52" if inflation < 4 else "#EF553B")
    spread_color = "#EF553B" if spread_val < 0 else "#00CC96"
    hy_color = "#00CC96" if hy < 4 else ("#FECB52" if hy < 6 else "#EF553B")

    return dbc.Row([
        make_kpi_card("S&P 500 YTD", f"{spy_return:+.1f}%",
                      "Broad market", spy_color),
        make_kpi_card("VIX", f"{vix_val:.1f}",
                      "Low fear" if vix_val < 20
                      else ("Elevated" if vix_val < 30 else "Panic"),
                      vix_color),
        make_kpi_card("Inflation", f"{inflation:.1f}%",
                      "Cuts possible" if inflation < 2.5
                      else "Rates stay high", infl_color),
        make_kpi_card("Fed Rate", f"{fed_rate:.2f}%",
                      "Higher = pressure"),
        make_kpi_card("Yield Spread", f"{spread_val:+.2f}%",
                      "Inverted = recession risk" if spread_val < 0
                      else "Normal curve", spread_color),
        make_kpi_card("Credit Spread", f"{hy:.2f}%",
                      "Tight = risk-on" if hy < 4
                      else "Widening = stress", hy_color),
    ], className="mb-4")


# ── Helper: market takeaways ─────────────────────────────────────────────────

def build_takeaways(df, spread, prices):
    points = []

    # 1. Market trend
    spy = prices["SPY"].dropna()
    sma50 = spy.rolling(50).mean().iloc[-1]
    sma200 = spy.rolling(200).mean().iloc[-1]
    spy_last = spy.iloc[-1]

    if spy_last > sma50 > sma200:
        points.append(
            f"Trend is bullish — SPY (${spy_last:.0f}) is above both its "
            f"50-day (${sma50:.0f}) and 200-day (${sma200:.0f}) moving averages."
        )
    elif spy_last < sma50 < sma200:
        points.append(
            f"Trend is bearish — SPY (${spy_last:.0f}) is below both its "
            f"50-day (${sma50:.0f}) and 200-day (${sma200:.0f}) moving averages."
        )
    elif spy_last < sma200:
        points.append(
            f"Caution — SPY (${spy_last:.0f}) is below the 200-day SMA "
            f"(${sma200:.0f}), which many consider the line between uptrend "
            f"and downtrend."
        )
    else:
        points.append(
            f"Mixed signals — SPY (${spy_last:.0f}) holds above the 200-day "
            f"(${sma200:.0f}) but is choppy around the 50-day (${sma50:.0f})."
        )

    # 2. Fear gauge
    vix_val = df["VIX"].dropna().iloc[-1]
    hy = df["High Yield Spread"].dropna().iloc[-1]

    if vix_val > 30:
        points.append(
            f"Fear is elevated — VIX at {vix_val:.1f}, credit spreads at "
            f"{hy:.2f}%. Historically, high-fear periods have been better "
            f"buying opportunities than selling ones."
        )
    elif vix_val < 15 and hy < 3.5:
        points.append(
            f"Markets are calm — VIX at {vix_val:.1f}, tight credit spreads "
            f"({hy:.2f}%). Low volatility can mean complacency."
        )
    else:
        points.append(
            f"Risk appetite is moderate — VIX at {vix_val:.1f}, credit "
            f"spreads at {hy:.2f}%. Neither fearful nor euphoric."
        )

    # 3. Fed & inflation
    inflation = df["CPI Inflation (Trimmed Mean)"].dropna().iloc[-1]
    fed_rate = df["Federal Funds Rate"].dropna().iloc[-1]

    if inflation > 3:
        points.append(
            f"Inflation at {inflation:.1f}% keeps the Fed hawkish "
            f"(rate at {fed_rate:.2f}%). High rates weigh on stock "
            f"valuations, especially growth names."
        )
    elif inflation > 2.3:
        points.append(
            f"Inflation at {inflation:.1f}% — close to the 2% target but "
            f"not there yet. The Fed is likely on hold at {fed_rate:.2f}%."
        )
    else:
        points.append(
            f"Inflation at {inflation:.1f}% gives the Fed room to cut from "
            f"{fed_rate:.2f}%. Rate cuts are the biggest catalyst for "
            f"higher stock prices."
        )

    return dbc.Card(dbc.CardBody([
        html.H5("Quick Take", className="mb-3"),
        html.Ul([html.Li(html.Span(p), className="mb-2") for p in points],
                style={"paddingLeft": "1.2rem", "lineHeight": "1.6"}),
    ]), className="bg-dark border-secondary mb-4")


# ── Layout ────────────────────────────────────────────────────────────────────
app.layout = dbc.Container([

    # Header
    dbc.Row(dbc.Col(html.H1(
        "Macro-Equity Dashboard",
        className="text-center my-4",
    ))),
    dbc.Row(dbc.Col(html.P(
        "How macro indicators drive the stock market. "
        "Live data from FRED & Yahoo Finance.",
        className="text-center text-muted mb-2",
    ))),

    # KPI cards + takeaways
    html.Div(id="kpi-row"),
    html.Div(id="takeaways"),

    # ── Market Pulse ──────────────────────────────────────────────────────────
    html.Hr(),
    html.H3("Market Pulse", className="mt-4 mb-1"),
    html.P("Is the market trending up or down, and how scared are investors?",
           className="text-muted mb-3"),
    dbc.Row([
        dbc.Col(dcc.Graph(id="sp500-sma"), md=6),
        dbc.Col(dcc.Graph(id="vix-chart"), md=6),
    ]),

    # ── The Macro Backdrop ────────────────────────────────────────────────────
    html.Hr(),
    html.H3("The Macro Backdrop", className="mt-4 mb-1"),
    html.P("The three forces that shape where stocks go next: "
           "inflation, the yield curve, and the Fed.",
           className="text-muted mb-3"),
    dbc.Row([
        dbc.Col(dcc.Graph(id="inflation-chart"), md=6),
        dbc.Col(dcc.Graph(id="yield-spread"), md=6),
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id="fed-unemployment"), md=6),
    ]),

    # ── Sector Breakdown ─────────────────────────────────────────────────────
    html.Hr(),
    html.H3("Sector Breakdown", className="mt-4 mb-1"),
    html.P("Where is money flowing, and which sectors are giving "
           "the best return for the risk?",
           className="text-muted mb-3"),

    # Heatmap + bar
    dbc.Row([
        dbc.Col(dcc.Graph(id="sector-heatmap"), md=7),
        dbc.Col([
            html.Label("Period:", className="mb-2"),
            dcc.Dropdown(
                id="period-dropdown",
                options=[{"label": p, "value": p}
                         for p in ["1M", "3M", "6M", "YTD", "1Y"]],
                value="YTD",
                clearable=False,
                className="mb-3",
                style={"color": "#000"},
            ),
            dcc.Graph(id="sector-bar"),
        ], md=5),
    ]),

    # Risk vs Return
    dbc.Row(dbc.Col(dcc.Graph(id="risk-return-chart"), md=8),
            className="justify-content-center"),

    # Footer
    html.Hr(),
    html.P(
        "Data: FRED (Federal Reserve Economic Data) & Yahoo Finance. "
        "Refreshed hourly.",
        className="text-center text-muted my-4",
    ),

], fluid=True, className="dbc")


# ── Callbacks ─────────────────────────────────────────────────────────────────

@app.callback(
    [
        Output("kpi-row", "children"),
        Output("takeaways", "children"),
        Output("sp500-sma", "figure"),
        Output("vix-chart", "figure"),
        Output("inflation-chart", "figure"),
        Output("yield-spread", "figure"),
        Output("fed-unemployment", "figure"),
        Output("sector-heatmap", "figure"),
        Output("risk-return-chart", "figure"),
    ],
    [Input("sp500-sma", "id")],
)
def update_all_charts(_):
    df = load_fred()
    prices = load_sectors()

    spread = compute_yield_spread(df)
    ytd_returns = compute_sector_returns(prices, "YTD")
    spy_return = ytd_returns.get("SPY", 0.0)

    heatmap_data = {}
    for period in ["1M", "3M", "YTD", "1Y"]:
        heatmap_data[period] = compute_sector_returns(prices, period)

    rr = compute_risk_return(prices, "1Y")

    return (
        build_kpi_row(df, spread, spy_return),
        build_takeaways(df, spread, prices),
        sp500_sma_chart(prices["SPY"]),
        vix_chart(df["VIX"]),
        inflation_chart(df["CPI Inflation (Trimmed Mean)"]),
        yield_spread_chart(spread),
        fed_unemployment_chart(df),
        sector_heatmap(heatmap_data),
        risk_return_chart(rr),
    )


@app.callback(
    Output("sector-bar", "figure"),
    [Input("period-dropdown", "value")],
)
def update_sector_bar(period):
    prices = load_sectors()
    returns = compute_sector_returns(prices, period)
    return sector_bar_chart(returns, period)


if __name__ == "__main__":
    app.run(debug=True)
