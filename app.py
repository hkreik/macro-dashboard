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


# ── KPI Cards ─────────────────────────────────────────────────────────────────

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
        make_kpi_card("S&P 500 YTD", f"{spy_return:+.1f}%", "Broad market", spy_color),
        make_kpi_card("VIX", f"{vix_val:.1f}",
                      "Low fear" if vix_val < 20 else ("Elevated" if vix_val < 30 else "Panic"),
                      vix_color),
        make_kpi_card("Inflation", f"{inflation:.1f}%",
                      "Near target" if inflation < 2.5 else "Above target", infl_color),
        make_kpi_card("Fed Rate", f"{fed_rate:.2f}%", "Policy rate"),
        make_kpi_card("Yield Spread", f"{spread_val:+.2f}%",
                      "Inverted" if spread_val < 0 else "Normal", spread_color),
        make_kpi_card("Credit Spread", f"{hy:.2f}%",
                      "Tight = risk-on" if hy < 4 else "Widening = stress", hy_color),
    ], className="mb-4")


# ── Glossary ──────────────────────────────────────────────────────────────────

GLOSSARY = [
    ("S&P 500",
     "A list of the 500 largest U.S. companies. When people say 'the market is up,' "
     "they usually mean the S&P 500 is up. SPY is the ETF (fund) that tracks it."),
    ("Moving Average (50-day / 200-day)",
     "Take the last 50 (or 200) closing prices and average them. "
     "If today's price is above that average, the market has been trending up. "
     "Below it means trending down. The 200-day is the most watched line in finance."),
    ("VIX — Fear Index",
     "Measures how much uncertainty options traders are pricing into the market. "
     "Below 20 = calm. 20–30 = anxious. Above 30 = panic. "
     "It spikes during crises (COVID, 2008) and falls during quiet bull markets."),
    ("Federal Funds Rate",
     "The interest rate the Fed charges banks to borrow money overnight. "
     "When this goes up, all borrowing gets more expensive — mortgages, car loans, business loans. "
     "That slows the economy down, which is the Fed's tool for fighting inflation."),
    ("Inflation",
     "How fast prices are rising. The Fed targets 2% per year as healthy. "
     "Above 2% = the Fed raises rates to cool things down. "
     "Below 2% = the Fed can cut rates to stimulate growth."),
    ("Yield Curve (10Y-2Y Spread)",
     "The difference between the interest rate on a 10-year government bond and a 2-year bond. "
     "Normally, longer loans pay more interest — so this number is positive. "
     "When it goes negative ('inverted'), it means investors expect the economy to slow. "
     "Every U.S. recession since the 1970s was preceded by an inverted yield curve."),
    ("Credit Spread (High Yield)",
     "Extra interest that risky companies must pay to borrow money, compared to the U.S. government. "
     "When this is low (under 4%), investors are confident and willing to lend cheaply. "
     "When it spikes, investors are scared and demand more compensation for risk — "
     "often a warning sign for stocks."),
    ("Sector ETFs (XLE, XLK, etc.)",
     "ETFs (funds) that hold stocks in a specific industry. XLK = tech companies, XLE = energy companies, etc. "
     "Watching which sectors lead vs lag tells you what investors expect next: "
     "if defensive sectors (utilities, staples) lead, investors are cautious. "
     "If growth sectors (tech, financials) lead, investors are optimistic."),
]


def build_glossary():
    items = []
    for term, definition in GLOSSARY:
        items.append(
            dbc.Col(
                html.Div([
                    html.Strong(term, style={"fontSize": "0.85rem", "color": "#FECB52"}),
                    html.P(definition, className="mb-0 mt-1",
                           style={"fontSize": "0.8rem", "lineHeight": "1.5", "color": "#adb5bd"}),
                ], className="mb-3"),
                md=6, lg=3,
            )
        )
    return dbc.Card(dbc.CardBody([
        html.H6("Key Terms — Read This First", className="mb-3 text-muted",
                style={"fontSize": "0.8rem", "textTransform": "uppercase", "letterSpacing": "0.05em"}),
        dbc.Row(items),
    ]), className="bg-dark border-secondary mb-4")


# ── Market Briefing ───────────────────────────────────────────────────────────

def build_briefing(df, spread, prices, returns):
    spy = prices["SPY"].dropna()
    sma50 = spy.rolling(50).mean().iloc[-1]
    sma200 = spy.rolling(200).mean().iloc[-1]
    spy_last = spy.iloc[-1]
    vix = df["VIX"].dropna().iloc[-1]
    inflation = df["CPI Inflation (Trimmed Mean)"].dropna().iloc[-1]
    fed_rate = df["Federal Funds Rate"].dropna().iloc[-1]
    spread_val = spread.dropna().iloc[-1]
    hy = df["High Yield Spread"].dropna().iloc[-1]

    # ── Sentence 1: Where is the market right now? ──
    if spy_last > sma50 > sma200:
        market_state = (
            f"The S&P 500 is currently at ${spy_last:.0f} and in a clear uptrend — "
            f"price is above both the 50-day (${sma50:.0f}) and 200-day (${sma200:.0f}) moving averages, "
            "which professionals use as the primary gauge of market direction."
        )
    elif spy_last < sma50 < sma200:
        market_state = (
            f"The S&P 500 is at ${spy_last:.0f} and in a downtrend — "
            f"price has fallen below both the 50-day (${sma50:.0f}) and 200-day (${sma200:.0f}) moving averages. "
            "This pattern, called a 'death cross,' signals that sellers are in control."
        )
    elif spy_last < sma200:
        market_state = (
            f"The S&P 500 is at ${spy_last:.0f} and has broken below its 200-day moving average "
            f"(${sma200:.0f}) — the key line most analysts use to separate bull and bear markets. "
            "This is a cautionary signal."
        )
    else:
        market_state = (
            f"The S&P 500 is at ${spy_last:.0f}, holding above its long-term 200-day average "
            f"(${sma200:.0f}) but struggling around the 50-day (${sma50:.0f}). "
            "The longer-term trend is intact, but near-term momentum has stalled."
        )

    # ── Sentence 2: Why? The macro backdrop ──
    if inflation < 2.5 and spread_val > 0:
        macro_why = (
            f"The economic backdrop is supportive: inflation has cooled to {inflation:.1f}%, "
            f"close to the Fed's 2% target, and the yield curve is healthy ({spread_val:+.2f}pp). "
            f"The Fed has room to lower its interest rate from {fed_rate:.2f}%, which makes borrowing cheaper "
            "for businesses and consumers — and cheaper borrowing typically drives stocks higher."
        )
    elif spread_val < 0:
        macro_why = (
            f"There's a warning signal in the bond market: the yield curve is inverted "
            f"({spread_val:+.2f}pp), meaning investors are currently earning more interest on "
            "short-term government bonds than long-term ones. That's backwards from normal, and it "
            "has happened before every U.S. recession since the 1970s — though a recession can "
            f"still be 1–2 years away. Inflation is at {inflation:.1f}% and the Fed rate is {fed_rate:.2f}%."
        )
    else:
        macro_why = (
            f"The Federal Reserve has kept its rate at {fed_rate:.2f}% because inflation ({inflation:.1f}%) "
            "hasn't fully come back down to its 2% goal. When rates are high, it costs more for companies "
            "to borrow and expand — which slows earnings growth and makes stocks, especially tech stocks, "
            "less attractive compared to bonds that now pay decent interest."
        )

    # ── Sentence 3: Investor mood ──
    if vix > 30:
        mood = (
            f"Investor fear is high — the VIX fear index is at {vix:.1f} and credit spreads are at {hy:.2f}%. "
            "When these spike together, it means both stock and bond markets are pricing in real stress. "
            "Historically, extreme fear has marked better buying opportunities than selling ones — "
            "but volatility tends to stay elevated until there is clarity on the underlying concern."
        )
    elif vix > 20:
        mood = (
            f"Investors are cautious but not panicking — the VIX is at {vix:.1f}, above the 20 threshold "
            f"that signals elevated anxiety, and credit spreads are at {hy:.2f}%. "
            "This kind of environment often reflects uncertainty rather than a specific crisis."
        )
    else:
        mood = (
            f"Markets are calm — the VIX fear index is at {vix:.1f} and credit spreads are tight at {hy:.2f}%. "
            "Low volatility means investors aren't pricing in near-term risk. "
            "That can be a good sign, though it can also reflect complacency before a surprise."
        )

    # ── Sentence 4: What to watch ──
    if len(returns) > 0:
        top = returns.index[0]
        defensive = top in ("XLU", "XLP", "XLV", "XLRE")
        watch = (
            f"One signal worth watching: {ETF_NAMES.get(top, top)} is the top-performing sector right now. "
            + (
                "Defensive sectors leading is often a sign that investors are rotating away from risk — "
                "they'd rather own stable, dividend-paying companies than bet on growth."
                if defensive else
                "Cyclical sectors leading suggests investors expect the economy to keep growing — "
                "they're willing to take on more risk for higher returns."
            )
        )
    else:
        watch = ""

    paragraphs = [market_state, macro_why, mood]
    if watch:
        paragraphs.append(watch)

    return dbc.Card(dbc.CardBody([
        dbc.Row([
            dbc.Col([
                html.H5("Market Briefing", className="mb-3"),
                *[html.P(p, className="mb-2", style={"lineHeight": "1.7", "fontSize": "0.95rem"})
                  for p in paragraphs],
                html.P(
                    "Generated from live FRED & Yahoo Finance data.",
                    className="text-muted mb-0 mt-1",
                    style={"fontSize": "0.75rem"},
                ),
            ])
        ])
    ]), className="bg-dark border-secondary mb-4")


# ── Per-Chart Conclusions ─────────────────────────────────────────────────────

def chart_conclusion(text: str) -> html.Div:
    return html.Div(
        html.P(text, className="text-muted", style={"fontSize": "0.9rem", "lineHeight": "1.6"}),
        className="px-2 pb-3",
    )


def trend_conclusion(prices):
    spy = prices["SPY"].dropna()
    sma50 = spy.rolling(50).mean().iloc[-1]
    sma200 = spy.rolling(200).mean().iloc[-1]
    spy_last = spy.iloc[-1]

    if spy_last > sma50 > sma200:
        return chart_conclusion(
            f"The S&P 500 (${spy_last:.0f}) is above both its 50-day (${sma50:.0f}) and "
            f"200-day (${sma200:.0f}) moving averages — a classic sign of a healthy uptrend. "
            "When price is above the 200-day, most professional investors consider the market "
            "to be in bull territory."
        )
    elif spy_last < sma50 < sma200:
        return chart_conclusion(
            f"The S&P 500 (${spy_last:.0f}) is below both moving averages — a bearish signal. "
            f"The 50-day (${sma50:.0f}) has crossed below the 200-day (${sma200:.0f}), "
            "which traders call a 'death cross.' This historically precedes further weakness."
        )
    elif spy_last < sma200:
        return chart_conclusion(
            f"Caution: the S&P 500 (${spy_last:.0f}) has broken below the 200-day moving average "
            f"(${sma200:.0f}). This is the line most analysts watch as the dividing line between "
            "bull and bear markets."
        )
    else:
        return chart_conclusion(
            f"The S&P 500 (${spy_last:.0f}) is holding above its 200-day average (${sma200:.0f}) "
            f"but below the 50-day (${sma50:.0f}) — a mixed signal. The longer-term trend is still "
            "up, but short-term momentum has stalled."
        )


def stress_conclusion(df):
    vix = df["VIX"].dropna().iloc[-1]
    hy = df["High Yield Spread"].dropna().iloc[-1]

    if vix > 30 or hy > 6:
        return chart_conclusion(
            f"Stress indicators are elevated — VIX at {vix:.1f} and credit spreads at {hy:.2f}%. "
            "When these two rise together, it signals that both equity and bond markets are pricing "
            "in risk. Historically, peaks in VIX have been good long-term buying opportunities, "
            "but they can signal more short-term pain ahead."
        )
    elif vix < 15 and hy < 3.5:
        return chart_conclusion(
            f"Markets are unusually calm — VIX at {vix:.1f}, credit spreads tight at {hy:.2f}%. "
            "Low volatility isn't always positive: it can signal complacency. Warren Buffett's "
            "'be fearful when others are greedy' applies here."
        )
    else:
        return chart_conclusion(
            f"Risk appetite is moderate — VIX at {vix:.1f} and credit spreads at {hy:.2f}%. "
            "Neither panic nor euphoria. Credit spreads are particularly important: when they widen "
            "sharply, it often precedes equity selloffs by several weeks."
        )


def fed_conclusion(df):
    inflation = df["CPI Inflation (Trimmed Mean)"].dropna().iloc[-1]
    fed_rate = df["Federal Funds Rate"].dropna().iloc[-1]

    if inflation > 3:
        return chart_conclusion(
            f"Inflation at {inflation:.1f}% is well above the Fed's 2% target, keeping the Fed "
            f"hawkish at {fed_rate:.2f}%. High interest rates make borrowing expensive for companies, "
            "which compresses profit margins and puts pressure on stock valuations — especially "
            "high-growth tech stocks whose value depends on future earnings."
        )
    elif inflation > 2.3:
        return chart_conclusion(
            f"Inflation at {inflation:.1f}% is close to the Fed's 2% target but not there yet. "
            f"The Fed is likely on hold at {fed_rate:.2f}%. Markets are watching every CPI and PCE "
            "report closely. A sustained move below 2.5% would open the door to rate cuts, "
            "which are historically a strong catalyst for equity rallies."
        )
    else:
        return chart_conclusion(
            f"Inflation at {inflation:.1f}% is near the Fed's 2% target, giving it room to lower "
            f"its rate from {fed_rate:.2f}%. When the Fed cuts rates, borrowing becomes cheaper for "
            "everyone — businesses can invest more, consumers spend more, and investors move money "
            "from bonds into stocks, pushing stock prices up. Rate cuts are one of the most direct "
            "catalysts for a stock market rally."
        )


ETF_NAMES = {
    "SPY": "S&P 500 (SPY)", "QQQ": "Nasdaq 100 (QQQ)", "DIA": "Dow Jones (DIA)",
    "IWM": "Small Cap (IWM)", "XLK": "Technology (XLK)", "XLF": "Financials (XLF)",
    "XLE": "Energy (XLE)", "XLV": "Health Care (XLV)", "XLI": "Industrials (XLI)",
    "XLC": "Communication (XLC)", "XLY": "Consumer Discretionary (XLY)",
    "XLP": "Consumer Staples (XLP)", "XLU": "Utilities (XLU)",
    "XLRE": "Real Estate (XLRE)", "XLB": "Materials (XLB)",
}


def sector_conclusion(returns):
    if len(returns) == 0:
        return chart_conclusion("Sector data unavailable.")
    top = returns.index[0]
    bottom = returns.index[-1]
    top_val = returns.iloc[0]
    bottom_val = returns.iloc[-1]
    top_name = ETF_NAMES.get(top, top)
    bottom_name = ETF_NAMES.get(bottom, bottom)

    return chart_conclusion(
        f"{top_name} leads this period (+{top_val:.1f}%) while {bottom_name} lags ({bottom_val:+.1f}%). "
        "Sector rotation — money moving from one part of the market to another — is one of the "
        "most reliable signals of where the economy is in its cycle. Defensive sectors (Utilities, "
        "Consumer Staples, Health Care) typically lead when investors expect a slowdown; cyclical "
        "sectors (Technology, Consumer Discretionary, Financials) lead in expansions."
    )


def correlation_conclusion(corr_df):
    most_positive = corr_df["Correlation"].idxmax()
    most_negative = corr_df["Correlation"].idxmin()
    pos_val = corr_df.loc[most_positive, "Correlation"]
    neg_val = corr_df.loc[most_negative, "Correlation"]

    return chart_conclusion(
        f"Over the past 5 years, {most_positive} has the strongest positive correlation with "
        f"monthly S&P 500 returns (+{pos_val:.2f}), while {most_negative} has the strongest "
        f"negative correlation ({neg_val:.2f}). "
        "A correlation near +1 means the indicator tends to rise when stocks rise; near -1 means "
        "the opposite. This analysis was computed across 60 months of data to identify which macro "
        "variables have a statistically meaningful relationship with market performance."
    )


# ── Recession Score Panel ─────────────────────────────────────────────────────

COLOR_MAP = {"danger": "#EF553B", "warning": "#FECB52", "success": "#00CC96"}

def build_recession_panel(score_data):
    score = score_data["score"]
    signals = score_data["signals"]

    if score >= 60:
        gauge_color = "#EF553B"
        label = "High Risk"
    elif score >= 35:
        gauge_color = "#FECB52"
        label = "Moderate Risk"
    else:
        gauge_color = "#00CC96"
        label = "Low Risk"

    signal_rows = []
    for name, (description, severity) in signals.items():
        color = COLOR_MAP[severity]
        signal_rows.append(
            dbc.Row([
                dbc.Col(html.Strong(name, style={"fontSize": "0.85rem"}), md=3),
                dbc.Col(html.Span(description, style={"fontSize": "0.85rem", "color": color}), md=9),
            ], className="mb-2")
        )

    return dbc.Card(dbc.CardBody([
        dbc.Row([
            dbc.Col([
                html.H5("Recession Risk Score", className="mb-1"),
                html.Div([
                    html.Span(
                        f"{score}/100",
                        style={"fontSize": "2.5rem", "fontWeight": "bold", "color": gauge_color}
                    ),
                    html.Span(
                        f" — {label}",
                        style={"fontSize": "1rem", "color": gauge_color}
                    ),
                ]),
                html.P(
                    "A composite score built from 5 macro signals the Fed and economists "
                    "use to gauge recession probability. Each signal contributes up to 25 points.",
                    className="text-muted mt-2",
                    style={"fontSize": "0.85rem"},
                ),
            ], md=4),
            dbc.Col([
                html.H6("Signal Breakdown", className="mb-3 text-muted"),
                *signal_rows,
            ], md=8),
        ]),
    ]), className="bg-dark border-secondary mb-4")


# ── What the Data Says ────────────────────────────────────────────────────────

def build_synthesis(df, spread, prices, returns):
    points = []

    # Trend
    spy = prices["SPY"].dropna()
    spy_last = spy.iloc[-1]
    sma200 = spy.rolling(200).mean().iloc[-1]
    trend_word = "above" if spy_last > sma200 else "below"
    points.append(
        f"The S&P 500 is {trend_word} its 200-day moving average, "
        f"putting the broad market in {'bull' if trend_word == 'above' else 'bear'} territory."
    )

    # Macro regime
    inflation = df["CPI Inflation (Trimmed Mean)"].dropna().iloc[-1]
    fed_rate = df["Federal Funds Rate"].dropna().iloc[-1]
    spread_val = spread.dropna().iloc[-1]

    if inflation < 2.5 and spread_val > 0:
        points.append(
            f"The macro backdrop is constructive: inflation ({inflation:.1f}%) is near target and "
            f"the yield curve is positive ({spread_val:+.2f}pp). This combination has historically "
            "been favorable for equities."
        )
    elif spread_val < 0:
        points.append(
            f"The yield curve is inverted ({spread_val:+.2f}pp), which has preceded every U.S. "
            "recession since the 1970s. This doesn't mean a recession is imminent — the lag "
            "can be 12-24 months — but it warrants attention."
        )
    else:
        points.append(
            f"Inflation ({inflation:.1f}%) remains the key constraint on the Fed ({fed_rate:.2f}%). "
            "Until inflation is sustainably at 2%, rate cuts are unlikely, which caps valuations "
            "on long-duration assets like growth stocks."
        )

    # Sector signal
    if len(returns) > 0:
        top_sector = returns.index[0]
        points.append(
            f"Sector rotation shows {top_sector} leading — "
            f"{'a defensive signal, suggesting investors are cautious' if top_sector in ('XLU', 'XLP', 'XLV') else 'a risk-on signal, suggesting investors expect growth'}."
        )

    return dbc.Card(dbc.CardBody([
        html.H5("What the Data Says", className="mb-3"),
        html.Ul(
            [html.Li(html.Span(p), className="mb-2") for p in points],
            style={"paddingLeft": "1.2rem", "lineHeight": "1.7"},
        ),
        html.P(
            "These conclusions are generated programmatically from live FRED and Yahoo Finance data.",
            className="text-muted mb-0 mt-2",
            style={"fontSize": "0.8rem"},
        ),
    ]), className="bg-dark border-secondary mb-4")


# ── Layout ─────────────────────────────────────────────────────────────────────

LABEL_COLORS = {
    "Broad Market": "#636EFA",
    "Bond Market / Fed Policy": "#00CC96",
    "Market Volatility": "#EF553B",
}


def build_news_card(articles: list) -> dbc.Card:
    if not articles:
        rows = [html.P("No news available.", className="text-muted mb-0")]
    else:
        rows = []
        for a in articles:
            label = a.get("label", "")
            # Color: sector labels gold, others by map
            label_color = LABEL_COLORS.get(label, "#FECB52")
            rows.append(
                html.Div([
                    html.Div(
                        html.Span(label, style={
                            "fontSize": "0.68rem", "color": label_color,
                            "textTransform": "uppercase", "letterSpacing": "0.04em",
                            "fontWeight": "600",
                        }),
                        className="mb-1",
                    ),
                    html.A(
                        a["title"],
                        href=a["url"],
                        target="_blank",
                        style={"fontSize": "0.85rem", "color": "#e9ecef",
                               "textDecoration": "none", "lineHeight": "1.4"},
                    ),
                    html.Div(
                        f"{a['source']}  ·  {a['age']}",
                        className="text-muted mt-1",
                        style={"fontSize": "0.72rem"},
                    ),
                ], className="mb-3 pb-2 border-bottom border-secondary")
            )
    return dbc.Card(dbc.CardBody([
        html.H6("News Driving the Market", className="mb-3",
                style={"fontSize": "0.8rem", "textTransform": "uppercase",
                       "letterSpacing": "0.05em", "color": "#adb5bd"}),
        *rows,
        html.P("Via Yahoo Finance · Last 3 days", className="text-muted mb-0 mt-1",
               style={"fontSize": "0.7rem"}),
    ]), className="bg-dark border-secondary mb-4")


def section_header(title, subtitle):
    return [
        html.Hr(),
        html.H4(title, className="mt-4 mb-1"),
        html.P(subtitle, className="text-muted mb-3", style={"fontSize": "0.9rem"}),
    ]


app.layout = dbc.Container([

    # Header
    dbc.Row(dbc.Col(html.H2(
        "Macro-Equity Dashboard",
        className="text-center mt-4 mb-1",
    ))),
    dbc.Row(dbc.Col(html.P(
        "Live macro analysis — FRED & Yahoo Finance data, refreshed hourly.",
        className="text-center text-muted mb-4",
        style={"fontSize": "0.9rem"},
    ))),

    # ── Glossary ──────────────────────────────────────────────────────────────
    build_glossary(),

    # ── At a glance ───────────────────────────────────────────────────────────
    html.Div(id="kpi-row"),

    # ── Market Briefing (the story) ───────────────────────────────────────────
    dbc.Row([
        dbc.Col(html.Div(id="market-briefing"), md=8),
        dbc.Col(html.Div(id="news-card"), md=4),
    ]),

    # ── Recession Score ────────────────────────────────────────────────────────
    *section_header(
        "Recession Risk Score",
        "A composite score built from 5 signals economists and the Fed use to gauge recession risk. "
        "No single indicator is definitive — combining them gives a clearer picture.",
    ),
    html.Div(id="recession-panel"),

    # ── Supporting Charts ─────────────────────────────────────────────────────
    *section_header(
        "Supporting Charts",
        "The data behind the briefing above. Each chart answers one question.",
    ),

    # Chart 1: Market Trend
    html.H6("1. Is the market trending up or down?",
            className="mt-3 mb-1 text-muted"),
    dcc.Graph(id="sp500-sma"),
    html.Div(id="trend-conclusion"),

    # Chart 2: System Stress
    html.H6("2. How much stress is in the system?",
            className="mt-4 mb-1 text-muted"),
    dcc.Graph(id="stress-chart"),
    html.Div(id="stress-conclusion"),

    # Chart 3: Fed Policy
    html.H6("3. What is the Fed doing and why?",
            className="mt-4 mb-1 text-muted"),
    dcc.Graph(id="fed-policy-chart"),
    html.Div(id="fed-conclusion"),

    # Chart 4: Sector Rotation
    html.H6("4. Where is money flowing?", className="mt-4 mb-1 text-muted"),
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(
                id="period-dropdown",
                options=[{"label": p, "value": p}
                         for p in ["1M", "3M", "6M", "YTD", "1Y"]],
                value="YTD",
                clearable=False,
                style={"color": "#000", "maxWidth": "120px"},
            ),
        ], md=2),
    ], className="mb-2"),
    dcc.Graph(id="sector-bar"),
    html.Div(id="sector-conclusion"),

    # ── Data Analysis ──────────────────────────────────────────────────────────
    *section_header(
        "Data Analysis: Which Macro Indicators Actually Move Markets?",
        "Using 5 years of monthly data, I computed the Pearson correlation between each "
        "macro indicator and the S&P 500's return that same month. "
        "A value near -1 means the indicator tends to be high when stocks fall; near +1 means the opposite.",
    ),
    dcc.Graph(id="correlation-chart"),
    html.Div(id="correlation-conclusion"),

    # Footer
    html.Hr(),
    html.P(
        "Data: FRED (Federal Reserve Economic Data) & Yahoo Finance. Refreshed hourly.",
        className="text-center text-muted my-4",
        style={"fontSize": "0.8rem"},
    ),

], fluid=True, className="dbc")


# ── Callbacks ──────────────────────────────────────────────────────────────────

@app.callback(
    [
        Output("kpi-row", "children"),
        Output("market-briefing", "children"),
        Output("recession-panel", "children"),
        Output("sp500-sma", "figure"),
        Output("trend-conclusion", "children"),
        Output("stress-chart", "figure"),
        Output("stress-conclusion", "children"),
        Output("fed-policy-chart", "figure"),
        Output("fed-conclusion", "children"),
        Output("correlation-chart", "figure"),
        Output("correlation-conclusion", "children"),
        Output("news-card", "children"),
    ],
    [Input("sp500-sma", "id")],
)
def update_main(_):
    df = load_fred()
    prices = load_sectors()
    spread = compute_yield_spread(df)
    ytd_returns = compute_sector_returns(prices, "YTD")
    spy_return = ytd_returns.get("SPY", 0.0)
    corr_df = compute_macro_correlations(df, prices)
    recession = compute_recession_score(df)
    top_sector = ytd_returns.index[0] if len(ytd_returns) > 0 else None
    bottom_sector = ytd_returns.index[-1] if len(ytd_returns) > 0 else None
    vix_elevated = df["VIX"].dropna().iloc[-1] > 20
    news = get_market_news(top_sector=top_sector, bottom_sector=bottom_sector,
                           vix_elevated=vix_elevated)

    return (
        build_kpi_row(df, spread, spy_return),
        build_briefing(df, spread, prices, ytd_returns),
        build_recession_panel(recession),
        sp500_sma_chart(prices["SPY"]),
        trend_conclusion(prices),
        stress_chart(df["VIX"], df["High Yield Spread"]),
        stress_conclusion(df),
        fed_policy_chart(df),
        fed_conclusion(df),
        correlation_chart(corr_df),
        correlation_conclusion(corr_df),
        build_news_card(news),
    )


@app.callback(
    [Output("sector-bar", "figure"), Output("sector-conclusion", "children")],
    [Input("period-dropdown", "value")],
)
def update_sector(period):
    prices = load_sectors()
    returns = compute_sector_returns(prices, period)
    return sector_bar_chart(returns, period), sector_conclusion(returns)


if __name__ == "__main__":
    app.run(debug=True)
