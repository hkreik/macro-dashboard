"""
UI component builders for the Macro-Equity Dashboard.
Separated from app.py to keep the main module focused on routing and callbacks.
"""

from dash import html
import dash_bootstrap_components as dbc


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
                      "Normal" if hy < 4 else ("Elevated" if hy < 6 else "Wide"), hy_color),
    ])


def build_recession_panel(score_data: dict):
    score = score_data["score"]
    signals = score_data["signals"]

    if score >= 60:
        color = "#EF553B"
        label = "HIGH RISK"
    elif score >= 35:
        color = "#FECB52"
        label = "MODERATE RISK"
    else:
        color = "#00CC96"
        label = "LOW RISK"

    signal_rows = []
    for name, info in signals.items():
        status_color = "#EF553B" if "High" in info["status"] else (
            "#FECB52" if any(x in info["status"] for x in
                             ["Moderate", "Elevated", "Flat", "Rising", "Below", "Very Low"])
            else "#00CC96"
        )
        signal_rows.append(
            dbc.Row([
                dbc.Col(html.Span(name, style={"fontSize": "0.85rem"}), width=5),
                dbc.Col(html.Span(info["value"], style={"fontSize": "0.85rem", "color": "white"}), width=2),
                dbc.Col(html.Span(info["status"], style={"fontSize": "0.85rem", "color": status_color}), width=5),
            ], className="mb-1")
        )

    return dbc.Card(dbc.CardBody([
        dbc.Row([
            dbc.Col([
                html.P("Recession Risk Score", className="text-muted mb-1", style={"fontSize": "0.8rem"}),
                html.H1(str(score), style={"color": color, "fontSize": "3.5rem", "fontWeight": "bold", "lineHeight": "1"}),
                html.Span(label, style={"color": color, "fontSize": "0.85rem", "fontWeight": "bold"}),
                html.P("/100", className="text-muted", style={"fontSize": "0.75rem"}),
            ], md=3, className="text-center d-flex flex-column justify-content-center"),
            dbc.Col([
                html.P("Signal Breakdown", className="text-muted mb-2", style={"fontSize": "0.8rem"}),
                *signal_rows,
            ], md=9),
        ])
    ]), className="bg-dark border-secondary mb-4")


def build_market_briefing(df, spread, spy_return, recession_score):
    inflation = df["CPI Inflation (Trimmed Mean)"].dropna().iloc[-1]
    fed_rate = df["Federal Funds Rate"].dropna().iloc[-1]
    vix_val = df["VIX"].dropna().iloc[-1]
    spread_val = spread.dropna().iloc[-1]
    hy = df["High Yield Spread"].dropna().iloc[-1]
    unemp = df["Unemployment Rate"].dropna().iloc[-1]
    score = recession_score["score"]

    lines = []

    if spy_return > 5:
        lines.append(f"The S&P 500 is up {spy_return:+.1f}% YTD, reflecting broad market strength.")
    elif spy_return > 0:
        lines.append(f"The S&P 500 is modestly positive at {spy_return:+.1f}% YTD.")
    elif spy_return > -5:
        lines.append(f"The S&P 500 is slightly negative at {spy_return:+.1f}% YTD, signaling some weakness.")
    else:
        lines.append(f"The S&P 500 is down {spy_return:+.1f}% YTD, indicating significant market pressure.")

    if inflation > 4:
        lines.append(f"Inflation remains elevated at {inflation:.1f}%, well above the Fed's 2% target, keeping policy tight.")
    elif inflation > 2.5:
        lines.append(f"Inflation at {inflation:.1f}% is above the Fed's 2% target; the Fed is likely in a holding pattern.")
    else:
        lines.append(f"Inflation at {inflation:.1f}% is near the Fed's 2% target, giving room for potential rate cuts.")

    lines.append(f"The Federal Funds Rate stands at {fed_rate:.2f}%.")

    if spread_val < 0:
        lines.append(f"The yield curve is inverted ({spread_val:+.2f}%), a historically reliable recession warning signal.")
    elif spread_val < 0.5:
        lines.append(f"The yield curve is flat ({spread_val:+.2f}%), suggesting modest economic uncertainty.")
    else:
        lines.append(f"The yield curve is positively sloped ({spread_val:+.2f}%), consistent with a healthy expansion.")

    if vix_val > 30:
        lines.append(f"Market fear is elevated with VIX at {vix_val:.1f} -- investors are pricing in significant risk.")
    elif vix_val > 20:
        lines.append(f"VIX at {vix_val:.1f} reflects some market anxiety, though not panic-level stress.")
    else:
        lines.append(f"Market fear is low with VIX at {vix_val:.1f}, suggesting investor confidence.")

    if hy > 6:
        lines.append(f"High-yield credit spreads at {hy:.2f}% are wide, indicating credit market stress.")
    elif hy > 4:
        lines.append(f"High-yield spreads at {hy:.2f}% are elevated -- credit markets are cautious.")
    else:
        lines.append(f"Credit spreads are tight at {hy:.2f}%, consistent with a risk-on environment.")

    lines.append(f"Unemployment is at {unemp:.1f}%.")

    if score >= 60:
        lines.append(f"The composite Recession Risk Score is {score}/100 -- multiple warning signals are flashing simultaneously.")
    elif score >= 35:
        lines.append(f"The Recession Risk Score of {score}/100 suggests moderate caution is warranted.")
    else:
        lines.append(f"The Recession Risk Score of {score}/100 indicates low near-term recession risk.")

    return dbc.Card(dbc.CardBody([
        html.H6("Market Briefing", className="text-muted mb-3"),
        html.P(" ".join(lines), style={"lineHeight": "1.8", "fontSize": "0.92rem"}),
    ]), className="bg-dark border-secondary mb-4")


def build_news_panel(news_items: list):
    if not news_items:
        return html.Div()

    cards = []
    for item in news_items:
        title = item.get("title", "")
        summary = item.get("summary", "")
        link = item.get("link", "")
        date_str = item.get("date", "")

        if date_str:
            try:
                from datetime import datetime as dt
                parsed = dt.fromisoformat(date_str.replace("Z", "+00:00"))
                date_str = parsed.strftime("%b %d, %Y")
            except Exception:
                pass

        card_content = [
            html.A(title, href=link, target="_blank",
                   style={"color": "white", "textDecoration": "none", "fontWeight": "bold",
                          "fontSize": "0.88rem"}) if link else html.Span(title, style={"fontWeight": "bold", "fontSize": "0.88rem"}),
        ]
        if summary:
            card_content.append(html.P(summary, className="text-muted mt-1 mb-1",
                                       style={"fontSize": "0.78rem", "lineHeight": "1.4"}))
        if date_str:
            card_content.append(html.Small(date_str, className="text-muted"))

        cards.append(dbc.Col(dbc.Card(dbc.CardBody(card_content),
                                       className="bg-dark border-secondary h-100"), md=4, className="mb-3"))

    return dbc.Card(dbc.CardBody([
        html.H6("Market News", className="text-muted mb-3"),
        dbc.Row(cards),
    ]), className="bg-dark border-secondary mb-4")
