"""
layouts.py — Beginner-friendly learning dashboard components.

Philosophy: Every number has a plain-English label explaining what it means.
Every section has an expandable accordion explaining WHY it matters to stocks.
No jargon. No acronyms without explanation. Cause-and-effect language throughout.
"""

from datetime import datetime, timezone
import dash_bootstrap_components as dbc
from dash import html

# ── Colour palette (soft dark — readable, not intimidating) ──────────────────
C = {
    'bg':       '#111827',   # dark blue-gray
    'surface':  '#1F2937',   # card background
    'border':   '#374151',   # subtle border
    'accent':   '#60A5FA',   # soft blue
    'positive': '#34D399',   # green
    'negative': '#F87171',   # red
    'warning':  '#FBBF24',   # amber
    'text':     '#F9FAFB',   # near-white
    'subtext':  '#9CA3AF',   # gray
    'muted':    '#6B7280',   # dark gray
}

CARD = {
    'backgroundColor': C['surface'],
    'border': f"1px solid {C['border']}",
    'borderRadius': '8px',
    'padding': '18px 22px',
}


# ── Header ───────────────────────────────────────────────────────────────────

def build_header() -> html.Div:
    return html.Div(
        dbc.Container(
            dbc.Row([
                dbc.Col(html.Div([
                    html.Span('📈', style={'fontSize': '18px', 'marginRight': '10px'}),
                    html.Span('Stock Market Learning Dashboard', style={
                        'color': C['text'], 'fontWeight': '700', 'fontSize': '15px',
                    }),
                ], style={'display': 'flex', 'alignItems': 'center'}), width='auto'),
                dbc.Col(html.Span(
                    'Updated every hour  •  All data from public sources',
                    style={'color': C['subtext'], 'fontSize': '12px'}
                ), className='d-flex align-items-center justify-content-end'),
            ], align='center', className='py-3'),
            fluid=True,
        ),
        style={
            'backgroundColor': C['surface'],
            'borderBottom': f"1px solid {C['border']}",
        }
    )


# ── Section header with optional explainer accordion ─────────────────────────

def section_header(title: str, explainer: str = '') -> html.Div:
    """Bold section title + optional collapsible 'What does this mean?' box."""
    children = [
        html.H6(title, style={
            'color': C['text'], 'fontWeight': '700',
            'fontSize': '14px', 'marginBottom': '4px',
        }),
    ]
    if explainer:
        children.append(
            dbc.Accordion([
                dbc.AccordionItem(
                    html.P(explainer, style={
                        'color': C['subtext'], 'fontSize': '13px',
                        'lineHeight': '1.7', 'margin': '0',
                    }),
                    title='What does this mean? ▾',
                )
            ], start_collapsed=True, flush=True, style={
                'marginBottom': '8px',
                '--bs-accordion-bg': C['surface'],
                '--bs-accordion-border-color': C['border'],
                '--bs-accordion-btn-color': C['accent'],
                '--bs-accordion-btn-bg': C['surface'],
                '--bs-accordion-active-bg': C['surface'],
                '--bs-accordion-active-color': C['accent'],
                '--bs-accordion-body-padding-x': '0',
                '--bs-accordion-body-padding-y': '8px',
                'fontSize': '12px',
            })
        )
    children.append(html.Hr(style={
        'borderColor': C['border'], 'marginTop': '6px',
        'marginBottom': '16px', 'opacity': '1',
    }))
    return html.Div(children)


# ── Plain-English KPI card ────────────────────────────────────────────────────

def kpi_card(title: str, value: str, meaning: str, color: str = None) -> dbc.Col:
    """
    title:   Short label e.g. 'S&P 500 This Year'
    value:   The number e.g. '+8.3%'
    meaning: One plain-English sentence about what it means RIGHT NOW
    color:   Override border/value color
    """
    val_color = color or C['text']
    border_left = color or C['border']
    return dbc.Col(
        html.Div([
            html.Div(title, style={
                'color': C['subtext'], 'fontSize': '11px',
                'fontWeight': '600', 'marginBottom': '8px',
                'textTransform': 'uppercase', 'letterSpacing': '0.05em',
            }),
            html.Div(value, style={
                'color': val_color, 'fontSize': '26px',
                'fontWeight': '700', 'fontFamily': 'monospace',
                'lineHeight': '1', 'marginBottom': '8px',
            }),
            html.Div(meaning, style={
                'color': C['subtext'], 'fontSize': '12px',
                'lineHeight': '1.5',
            }),
        ], style={**CARD, 'borderLeft': f'3px solid {border_left}'}),
        xs=12, sm=6, md=4, lg=3, className='mb-3'
    )


# ── KPI row builder ───────────────────────────────────────────────────────────

def build_kpi_row(fred_df, spread, spy_return) -> html.Div:
    try:
        inflation = fred_df['CPI Inflation (Trimmed Mean)'].dropna().iloc[-1]
    except Exception:
        inflation = None

    try:
        fed_rate = fred_df['Federal Funds Rate'].dropna().iloc[-1]
    except Exception:
        fed_rate = None

    try:
        vix = fred_df['VIX'].dropna().iloc[-1]
    except Exception:
        vix = None

    try:
        spread_val = spread.dropna().iloc[-1]
    except Exception:
        spread_val = None

    try:
        unemp = fred_df['Unemployment Rate'].dropna().iloc[-1]
    except Exception:
        unemp = None

    try:
        sentiment = fred_df['Consumer Sentiment'].dropna().iloc[-1]
    except Exception:
        sentiment = None

    cards = []

    # S&P 500
    spy_color = C['positive'] if spy_return >= 0 else C['negative']
    spy_meaning = (
        'The broad US stock market is UP so far this year — investors are generally optimistic.'
        if spy_return >= 0
        else 'The broad US stock market is DOWN so far this year — investors are cautious or selling.'
    )
    cards.append(kpi_card('S&P 500 This Year', f'{spy_return:+.1f}%', spy_meaning, spy_color))

    # VIX
    if vix is not None:
        if vix < 15:
            vix_color = C['positive']
            vix_meaning = 'Very calm markets. Investors are not worried about big swings.'
        elif vix < 25:
            vix_color = C['text']
            vix_meaning = 'Normal level of uncertainty. Markets are moving but nothing alarming.'
        elif vix < 35:
            vix_color = C['warning']
            vix_meaning = 'Elevated fear. Investors expect larger-than-normal price swings soon.'
        else:
            vix_color = C['negative']
            vix_meaning = 'Panic mode. Markets are very uncertain — this level is rare and serious.'
        cards.append(kpi_card('Fear Index (VIX)', f'{vix:.1f}', vix_meaning, vix_color))

    # Fed Rate
    if fed_rate is not None:
        if fed_rate > 4:
            rate_meaning = 'Borrowing is expensive. This slows spending and can pressure stocks.'
        elif fed_rate > 2:
            rate_meaning = 'Rates are moderate. Borrowing costs are manageable for businesses.'
        else:
            rate_meaning = 'Borrowing is cheap. Low rates tend to push investors toward stocks.'
        cards.append(kpi_card('Fed Interest Rate', f'{fed_rate:.2f}%', rate_meaning, C['accent']))

    # Inflation
    if inflation is not None:
        if inflation > 4:
            infl_color = C['negative']
            infl_meaning = 'Inflation is high — prices rising fast. The Fed will likely keep rates high to fight this.'
        elif inflation > 2.5:
            infl_color = C['warning']
            infl_meaning = 'Inflation is above the 2% target. The Fed is watching this closely.'
        else:
            infl_color = C['positive']
            infl_meaning = 'Inflation is near the Fed\'s 2% target. This is healthy for the economy.'
        cards.append(kpi_card('Inflation Rate', f'{inflation:.1f}%', infl_meaning, infl_color))

    # Yield Curve
    if spread_val is not None:
        if spread_val < 0:
            spread_color = C['negative']
            spread_meaning = 'The yield curve is INVERTED — historically a warning sign that a recession may be coming.'
        else:
            spread_color = C['positive']
            spread_meaning = 'The yield curve is normal — long-term bonds pay more than short-term, which is healthy.'
        cards.append(kpi_card('Yield Curve (10Y−2Y)', f'{spread_val:+.2f}%', spread_meaning, spread_color))

    # Unemployment
    if unemp is not None:
        if unemp < 4:
            unemp_color = C['positive']
            unemp_meaning = 'Very low unemployment — most people who want jobs have them. Good for consumer spending.'
        elif unemp < 6:
            unemp_color = C['text']
            unemp_meaning = 'Unemployment is moderate. The job market is OK but not booming.'
        else:
            unemp_color = C['negative']
            unemp_meaning = 'High unemployment — many people are out of work, which hurts consumer spending and stocks.'
        cards.append(kpi_card('Unemployment', f'{unemp:.1f}%', unemp_meaning, unemp_color))

    return dbc.Row(cards)


# ── Recession risk panel ──────────────────────────────────────────────────────

SIGNAL_EXPLANATIONS = {
    'CURVE INV': 'Yield curve inverted — short-term rates higher than long-term. Happened before most recessions.',
    'FFR>10Y':   'The Fed\'s rate is above the 10-year Treasury rate — another sign policy may be too tight.',
    'VIX>30':    'Fear index above 30 — markets are in or near panic territory.',
    'HY>500bp':  'Junk bond spreads are wide — companies with weak credit are struggling to borrow.',
    'UNEMP↑':    'Unemployment has been rising over the past 3 months.',
    'SENT<60':   'Consumer confidence is very low — people feel pessimistic about the economy.',
}

def build_recession_panel(score_data: dict) -> html.Div:
    score   = score_data.get('score', 0)
    signals = score_data.get('signals', [])

    if score >= 60:
        color = C['negative']
        verdict = 'High recession risk'
        summary = 'Multiple warning signs are flashing. This does not mean a recession is certain, but the odds are elevated.'
    elif score >= 35:
        color = C['warning']
        verdict = 'Some warning signs'
        summary = 'A few indicators are concerning. Worth watching, but not a crisis signal yet.'
    else:
        color = C['positive']
        verdict = 'Low recession risk'
        summary = 'Most indicators look healthy. The economy appears to be on solid footing.'

    signal_pills = []
    for sig in signals:
        name = sig['name']
        triggered = sig.get('triggered', False)
        pill_color = C['negative'] if triggered else C['muted']
        explanation = SIGNAL_EXPLANATIONS.get(name, name)
        signal_pills.append(
            html.Span(name, title=explanation, style={
                'backgroundColor': f'{pill_color}22',
                'border': f'1px solid {pill_color}55',
                'color': pill_color,
                'fontSize': '11px', 'fontWeight': '600',
                'borderRadius': '4px', 'padding': '3px 9px',
                'marginRight': '6px', 'marginBottom': '6px',
                'display': 'inline-block', 'cursor': 'help',
            })
        )

    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Div(str(score), style={
                    'color': color, 'fontSize': '56px',
                    'fontWeight': '800', 'fontFamily': 'monospace', 'lineHeight': '1',
                }),
                html.Div('out of 100', style={
                    'color': C['muted'], 'fontSize': '12px', 'marginTop': '4px',
                }),
                html.Div(verdict, style={
                    'color': color, 'fontSize': '13px',
                    'fontWeight': '700', 'marginTop': '8px',
                }),
            ], xs=12, md=2, className='mb-3 mb-md-0'),
            dbc.Col([
                html.P(summary, style={
                    'color': C['text'], 'fontSize': '13px',
                    'lineHeight': '1.7', 'marginBottom': '12px',
                }),
                html.Div('Signals being tracked (red = triggered, gray = OK):', style={
                    'color': C['muted'], 'fontSize': '11px', 'marginBottom': '8px',
                }),
                html.Div(signal_pills, style={'display': 'flex', 'flexWrap': 'wrap'}),
                html.Div('Hover over each signal to see what it means.', style={
                    'color': C['muted'], 'fontSize': '11px', 'marginTop': '6px',
                    'fontStyle': 'italic',
                }),
            ], xs=12, md=10),
        ]),
    ], style={**CARD, 'borderLeft': f'3px solid {color}'})


# ── Market briefing (plain-English summary) ───────────────────────────────────

def build_market_briefing(fred_df, spread, spy_return) -> html.Div:
    bullets = []

    try:
        fed = fred_df['Federal Funds Rate'].dropna().iloc[-1]
        infl = fred_df['CPI Inflation (Trimmed Mean)'].dropna().iloc[-1]
        real = fed - infl
        if real > 1.5:
            bullets.append(('🏦', 'Fed Policy', f'The Fed\'s interest rate ({fed:.2f}%) is significantly higher than inflation ({infl:.1f}%). This is called a "restrictive" policy — it makes borrowing expensive to slow down the economy and cool inflation.'))
        elif real > 0:
            bullets.append(('🏦', 'Fed Policy', f'The Fed\'s rate ({fed:.2f}%) is slightly above inflation ({infl:.1f}%). Policy is mildly tight — the Fed is keeping a lid on things without slamming the brakes.'))
        else:
            bullets.append(('🏦', 'Fed Policy', f'The Fed\'s rate ({fed:.2f}%) is below inflation ({infl:.1f}%). This is called "loose" policy — cheap money encourages borrowing and investing, which can boost stocks.'))
    except Exception:
        pass

    try:
        sp = spread.dropna().iloc[-1]
        if sp < 0:
            bullets.append(('📉', 'Yield Curve', f'The yield curve is inverted (10Y−2Y = {sp:+.2f}%). Normally, long-term bonds pay more interest than short-term ones. When that flips, it often signals investors expect the economy to slow. This has preceded most US recessions.'))
        else:
            bullets.append(('📈', 'Yield Curve', f'The yield curve is normal (10Y−2Y = {sp:+.2f}%). Long-term bonds pay more than short-term ones — investors expect steady growth ahead.'))
    except Exception:
        pass

    try:
        vix = fred_df['VIX'].dropna().iloc[-1]
        hy  = fred_df['High Yield Spread'].dropna().iloc[-1]
        if vix >= 30 or hy >= 500:
            bullets.append(('⚡', 'Market Stress', f'Stress indicators are elevated: VIX at {vix:.1f} (fear index) and high-yield bond spreads at {hy:.0f}bp. This means investors are nervous and riskier companies are paying a lot more to borrow money.'))
        elif vix >= 20:
            bullets.append(('🟡', 'Market Stress', f'Markets are a bit anxious: VIX at {vix:.1f}. Some uncertainty but nothing extreme. High-yield spreads at {hy:.0f}bp are normal.'))
        else:
            bullets.append(('✅', 'Market Stress', f'Markets are calm: VIX at {vix:.1f} and credit spreads at {hy:.0f}bp. Investors are not particularly worried right now.'))
    except Exception:
        pass

    try:
        infl = fred_df['CPI Inflation (Trimmed Mean)'].dropna().iloc[-1]
        if infl > 4:
            bullets.append(('💸', 'Inflation', f'Inflation is running hot at {infl:.1f}%. When prices rise this fast, the Fed raises rates to slow things down — and higher rates tend to push stock prices lower.'))
        elif infl > 2:
            bullets.append(('💸', 'Inflation', f'Inflation is {infl:.1f}%, above the Fed\'s 2% target but manageable. The Fed may keep rates elevated until this comes down.'))
        else:
            bullets.append(('💸', 'Inflation', f'Inflation is {infl:.1f}% — near or below the Fed\'s 2% target. This is good: it means the Fed has less reason to raise rates, which is positive for stocks.'))
    except Exception:
        pass

    items = []
    for icon, theme, text in bullets:
        items.append(
            dbc.Col(html.Div([
                html.Div(f'{icon}  {theme.upper()}', style={
                    'color': C['subtext'], 'fontSize': '10px',
                    'fontWeight': '700', 'letterSpacing': '0.08em',
                    'marginBottom': '8px',
                }),
                html.P(text, style={
                    'color': C['text'], 'fontSize': '13px',
                    'lineHeight': '1.7', 'margin': '0',
                }),
            ], style={**CARD, 'height': '100%'}),
            xs=12, md=6, className='mb-3')
        )

    return dbc.Row(items)


# ── Sector panel with real names ──────────────────────────────────────────────

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
    'SPY':  'S&P 500 (Total Market)',
    'QQQ':  'Nasdaq 100 (Tech-Heavy)',
    'DIA':  'Dow Jones 30',
    'IWM':  'Small Cap Stocks',
}

SECTOR_EXPLAINERS = {
    'XLK':  'Technology companies (Apple, Microsoft, Nvidia). Sensitive to interest rates — high rates hurt because future profits are worth less today.',
    'XLF':  'Banks and financial companies. Profit from higher interest rates. Does well when the economy is growing.',
    'XLE':  'Oil and gas companies. Moves with oil prices, which depend on global supply and demand.',
    'XLV':  'Hospitals, drugmakers, insurance. Tends to hold up well during recessions — people still need healthcare.',
    'XLI':  'Factories, construction, transportation. Tied to economic growth — does well in expansions.',
    'XLC':  'Google, Meta, Netflix. Mix of tech-like growth companies and old-school media.',
    'XLY':  'Amazon, Tesla, restaurants, hotels. People buy discretionary items when confident — sensitive to recessions.',
    'XLP':  'Walmart, Procter & Gamble, food companies. Defensive — people buy basics regardless of the economy.',
    'XLU':  'Electric and gas utilities. Slow-growing but pay dividends. Hurt by higher interest rates.',
    'XLRE': 'REITs — companies that own property. Very sensitive to interest rates. Falls when rates rise.',
    'XLB':  'Steel, chemicals, mining. Moves with global economic activity and commodity prices.',
}


# ── News panel ────────────────────────────────────────────────────────────────

def build_news_panel(articles: list) -> html.Div:
    if not articles:
        return html.Div(
            'No news available right now.',
            style={'color': C['subtext'], 'fontSize': '13px', 'padding': '12px'}
        )

    rows = []
    for i, art in enumerate(articles[:10]):
        headline = art.get('headline', art.get('title', 'Untitled'))
        url      = art.get('url', '#')
        source   = art.get('source', '')
        created  = art.get('created', art.get('datetime', ''))
        try:
            ts = datetime.utcfromtimestamp(int(created)).strftime('%b %d, %H:%M')
        except Exception:
            ts = str(created)[:10]

        rows.append(html.Div([
            html.Div([
                html.Span(source.upper(), style={
                    'color': C['accent'], 'fontSize': '10px',
                    'fontWeight': '700', 'marginRight': '8px',
                }),
                html.Span(ts, style={'color': C['muted'], 'fontSize': '10px'}),
            ], style={'marginBottom': '3px'}),
            html.A(headline, href=url, target='_blank', style={
                'color': C['text'], 'fontSize': '13px',
                'textDecoration': 'none', 'lineHeight': '1.5',
                'display': 'block',
            }),
            html.Hr(style={
                'borderColor': C['border'], 'margin': '10px 0',
                'opacity': '0.6',
            }) if i < len(articles) - 1 else None,
        ]))

    return html.Div(rows, style=CARD)


# ── Footer ────────────────────────────────────────────────────────────────────

def build_footer() -> html.Div:
    return html.Div(
        dbc.Container(
            html.P([
                'Data sources: ',
                html.A('FRED (Federal Reserve)', href='https://fred.stlouisfed.org', target='_blank',
                       style={'color': C['accent']}),
                ' · ',
                html.A('Yahoo Finance', href='https://finance.yahoo.com', target='_blank',
                       style={'color': C['accent']}),
                ' · ',
                html.A('Benzinga News', href='https://benzinga.com', target='_blank',
                       style={'color': C['accent']}),
                f'  •  Generated {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}',
            ], style={'color': C['muted'], 'fontSize': '11px', 'margin': '0'}),
            fluid=True,
        ),
        style={
            'borderTop': f"1px solid {C['border']}",
            'padding': '16px 0', 'marginTop': '40px',
            'backgroundColor': C['surface'],
        }
    )
