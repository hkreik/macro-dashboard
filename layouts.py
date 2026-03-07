"""
layouts.py — Industry-grade UI component builders.

Design language: Bloomberg/Refinitiv-inspired dark theme.
  Background:  #0D1117
  Surface:     #161B22
  Border:      #21262D
  Accent:      #58A6FF
  Positive:    #3FB950
  Negative:    #F85149
  Text:        #E6EDF3
"""

from datetime import datetime, timezone
import dash_bootstrap_components as dbc
from dash import html

C = {
    'bg':       '#0D1117',
    'surface':  '#161B22',
    'border':   '#21262D',
    'accent':   '#58A6FF',
    'positive': '#3FB950',
    'negative': '#F85149',
    'warning':  '#D29922',
    'neutral':  '#8B949E',
    'text':     '#E6EDF3',
    'subtext':  '#8B949E',
    'muted':    '#484F58',
}

CARD_STYLE = {
    'backgroundColor': C['surface'],
    'border': f"1px solid {C['border']}",
    'borderRadius': '6px',
    'padding': '16px 20px',
}


def build_header() -> html.Div:
    now_str = datetime.now(timezone.utc).strftime('%H:%M UTC')
    return html.Div(
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Span('M', style={
                            'backgroundColor': C['accent'], 'color': C['bg'],
                            'fontWeight': '800', 'fontSize': '13px',
                            'borderRadius': '4px', 'padding': '2px 7px',
                            'marginRight': '10px', 'fontFamily': 'monospace',
                        }),
                        html.Span('MACRO DASHBOARD', style={
                            'color': C['text'], 'fontWeight': '600',
                            'fontSize': '13px', 'letterSpacing': '0.12em',
                        }),
                    ], style={'display': 'flex', 'alignItems': 'center'}),
                ], width='auto'),
                dbc.Col([
                    html.Div([
                        html.Span(style={
                            'display': 'inline-block', 'width': '7px', 'height': '7px',
                            'borderRadius': '50%', 'backgroundColor': C['positive'],
                            'marginRight': '6px',
                        }),
                        html.Span('LIVE DATA', style={
                            'color': C['positive'], 'fontSize': '10px',
                            'fontWeight': '700', 'letterSpacing': '0.1em',
                        }),
                    ], style={
                        'display': 'inline-flex', 'alignItems': 'center',
                        'backgroundColor': 'rgba(63,185,80,0.1)',
                        'border': f"1px solid {C['positive']}44",
                        'borderRadius': '20px', 'padding': '3px 10px',
                    }),
                ], className='d-flex justify-content-center align-items-center'),
                dbc.Col([
                    html.Div([
                        html.Span(now_str, id='live-clock', style={
                            'color': C['subtext'], 'fontSize': '12px',
                            'fontFamily': 'monospace', 'marginRight': '14px',
                        }),
                        html.Span('1H CACHE', style={
                            'color': C['muted'], 'fontSize': '10px',
                            'letterSpacing': '0.06em', 'backgroundColor': C['border'],
                            'borderRadius': '4px', 'padding': '2px 7px',
                        }),
                    ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'flex-end'}),
                ], width='auto'),
            ], align='center', className='py-2'),
        ], fluid=True),
        style={
            'backgroundColor': C['surface'],
            'borderBottom': f"1px solid {C['border']}",
            'position': 'sticky', 'top': '0', 'zIndex': '1000',
        }
    )


def section_label(title: str, subtitle: str = '') -> html.Div:
    return html.Div([
        html.Div([
            html.Div(style={
                'width': '3px', 'height': '14px', 'backgroundColor': C['accent'],
                'borderRadius': '2px', 'marginRight': '10px', 'flexShrink': '0',
            }),
            html.Span(title, style={
                'color': C['text'], 'fontWeight': '600', 'fontSize': '11px',
                'letterSpacing': '0.1em', 'textTransform': 'uppercase',
            }),
            html.Span(f'  {subtitle}', style={
                'color': C['subtext'], 'fontSize': '11px', 'marginLeft': '8px',
            }) if subtitle else None,
        ], style={'display': 'flex', 'alignItems': 'center'}),
        html.Hr(style={
            'borderColor': C['border'], 'marginTop': '8px',
            'marginBottom': '16px', 'opacity': '1',
        }),
    ])


def make_kpi_card(title, value, subtitle='', color='white'):
    border_color = color if color not in ('white', '#FFFFFF', '') else C['accent']
    delta_el = None

    if subtitle and subtitle[0] in ('+', '-'):
        try:
            num = float(subtitle.split()[0].rstrip('%'))
            arrow = '▲' if num > 0 else '▼'
            delta_color = C['positive'] if num > 0 else C['negative']
            border_color = delta_color
            rest = ' '.join(subtitle.split()[1:]) if len(subtitle.split()) > 1 else ''
            delta_el = html.Div([
                html.Span(f'{arrow} {abs(num):.2f}', style={
                    'color': delta_color, 'fontSize': '11px',
                    'fontWeight': '600', 'fontFamily': 'monospace',
                }),
                html.Span(f'  {rest}', style={
                    'color': C['muted'], 'fontSize': '10px', 'marginLeft': '4px',
                }),
            ], style={'marginTop': '5px'})
        except (ValueError, IndexError):
            pass

    if delta_el is None and subtitle:
        delta_el = html.Div(subtitle, style={
            'color': C['subtext'], 'fontSize': '11px', 'marginTop': '5px',
        })

    inner = html.Div([
        html.Div(title.upper(), style={
            'color': C['subtext'], 'fontSize': '10px', 'fontWeight': '600',
            'letterSpacing': '0.1em', 'marginBottom': '8px',
        }),
        html.Div(value, style={
            'color': C['text'], 'fontSize': '22px', 'fontWeight': '700',
            'fontFamily': 'monospace', 'lineHeight': '1',
        }),
        delta_el or html.Div(style={'height': '16px'}),
    ], style={**CARD_STYLE, 'borderLeft': f'3px solid {border_color}'})

    return dbc.Col(inner, md=2, sm=4, xs=6, className='mb-3')


def build_kpi_row(df, spread, spy_return):
    inflation  = df['CPI Inflation (Trimmed Mean)'].dropna().iloc[-1]
    fed_rate   = df['Federal Funds Rate'].dropna().iloc[-1]
    vix_val    = df['VIX'].dropna().iloc[-1]
    spread_val = spread.dropna().iloc[-1]
    hy         = df['High Yield Spread'].dropna().iloc[-1]

    spy_color    = C['positive'] if spy_return >= 0 else C['negative']
    vix_color    = C['positive'] if vix_val < 20 else (C['warning'] if vix_val < 30 else C['negative'])
    infl_color   = C['positive'] if inflation < 2.5 else (C['warning'] if inflation < 4 else C['negative'])
    spread_color = C['negative'] if spread_val < 0 else C['positive']
    hy_color     = C['positive'] if hy < 4 else (C['warning'] if hy < 6 else C['negative'])

    return dbc.Row([
        make_kpi_card('S&P 500 YTD',  f'{spy_return:+.1f}%', 'Broad market',   spy_color),
        make_kpi_card('VIX',           f'{vix_val:.1f}',
                      'Low fear' if vix_val < 20 else ('Elevated' if vix_val < 30 else 'Panic'), vix_color),
        make_kpi_card('Inflation',     f'{inflation:.1f}%',
                      'Near target' if inflation < 2.5 else 'Above target', infl_color),
        make_kpi_card('Fed Rate',      f'{fed_rate:.2f}%', 'Policy rate', C['accent']),
        make_kpi_card('Yield Spread',  f'{spread_val:+.2f}%',
                      'Inverted' if spread_val < 0 else 'Normal', spread_color),
        make_kpi_card('Credit Spread', f'{hy:.2f}%',
                      'Normal' if hy < 4 else ('Elevated' if hy < 6 else 'Wide'), hy_color),
    ])


def build_recession_panel(score_data: dict) -> html.Div:
    score   = score_data['score']
    signals = score_data['signals']

    if score >= 60:
        regime_label = 'HIGH RISK'
        regime_color = C['negative']
        bg_tint      = 'rgba(248,81,73,0.05)'
    elif score >= 35:
        regime_label = 'ELEVATED'
        regime_color = C['warning']
        bg_tint      = 'rgba(210,153,34,0.05)'
    else:
        regime_label = 'LOW RISK'
        regime_color = C['positive']
        bg_tint      = 'rgba(63,185,80,0.05)'

    bar_blocks = []
    for i in range(5):
        filled = score >= i * 20 + 1
        bar_blocks.append(html.Div(style={
            'flex': '1', 'height': '5px', 'borderRadius': '3px',
            'backgroundColor': regime_color if filled else C['border'],
            'marginRight': '3px' if i < 4 else '0',
        }))

    pills = []
    for name, info in signals.items():
        status    = info.get('status', '')
        triggered = any(x in status for x in ['High', 'Elevated', 'Inverted', 'Rising', 'Very Low', 'Below', 'Flat', 'Moderate'])
        pill_color = C['negative'] if 'High' in status else (C['warning'] if triggered else C['muted'])
        pills.append(html.Div([
            html.Span('●', style={'color': pill_color, 'fontSize': '8px', 'marginRight': '5px'}),
            html.Div([
                html.Div(name, style={
                    'color': C['text'] if triggered else C['subtext'],
                    'fontSize': '11px', 'fontWeight': '500',
                }),
                html.Div(f"{info.get('value','')}  {status}", style={
                    'color': pill_color, 'fontSize': '10px', 'fontFamily': 'monospace',
                }),
            ]),
        ], style={
            'display': 'flex', 'alignItems': 'flex-start',
            'backgroundColor': f'{pill_color}11',
            'border': f'1px solid {pill_color}33',
            'borderRadius': '5px', 'padding': '5px 10px',
            'marginRight': '6px', 'marginBottom': '6px',
        }))

    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Div(str(score), style={
                    'color': regime_color, 'fontSize': '52px',
                    'fontWeight': '800', 'fontFamily': 'monospace', 'lineHeight': '1',
                }),
                html.Div('/ 100', style={
                    'color': C['muted'], 'fontSize': '13px',
                    'fontFamily': 'monospace', 'marginTop': '2px',
                }),
                html.Div(bar_blocks, style={'display': 'flex', 'marginTop': '10px', 'width': '110px'}),
                html.Div(regime_label, style={
                    'color': regime_color, 'fontSize': '10px',
                    'fontWeight': '700', 'letterSpacing': '0.12em', 'marginTop': '8px',
                }),
            ], xs=12, md=3, className='mb-3 mb-md-0'),
            dbc.Col([
                html.Div('RISK SIGNALS', style={
                    'color': C['subtext'], 'fontSize': '10px',
                    'letterSpacing': '0.1em', 'marginBottom': '10px',
                }),
                html.Div(pills, style={'display': 'flex', 'flexWrap': 'wrap'}),
            ], xs=12, md=9),
        ]),
    ], style={**CARD_STYLE, 'backgroundColor': bg_tint, 'borderLeft': f'3px solid {regime_color}'})


def build_market_briefing(df, spread, spy_return) -> html.Div:
    inflation  = df['CPI Inflation (Trimmed Mean)'].dropna().iloc[-1]
    fed_rate   = df['Federal Funds Rate'].dropna().iloc[-1]
    vix_val    = df['VIX'].dropna().iloc[-1]
    spread_val = spread.dropna().iloc[-1]
    hy         = df['High Yield Spread'].dropna().iloc[-1]
    real_rate  = fed_rate - inflation

    insights = [
        {
            'theme': 'MONETARY POLICY', 'icon': '🏦',
            'headline': 'Restrictive' if real_rate > 1.5 else ('Mildly Tight' if real_rate > 0 else 'Accommodative'),
            'stat': f'Fed Rate {fed_rate:.2f}%  |  Real Rate {real_rate:+.2f}%',
            'detail': 'Positive real rate tightens conditions' if real_rate > 0 else 'Negative real rate — still loose',
            'color': C['negative'] if real_rate > 1.5 else (C['warning'] if real_rate > 0 else C['positive']),
        },
        {
            'theme': 'YIELD CURVE', 'icon': '📉' if spread_val < 0 else '📈',
            'headline': 'Inverted' if spread_val < 0 else 'Normal',
            'stat': f'2/10 Spread: {spread_val:+.2f}%',
            'detail': 'Recession signal active' if spread_val < 0 else 'Healthy term structure',
            'color': C['negative'] if spread_val < 0 else C['positive'],
        },
        {
            'theme': 'INFLATION', 'icon': '💹',
            'headline': f'{inflation:.1f}% YoY',
            'stat': 'Above target' if inflation > 2 else 'Near target',
            'detail': f'Fed target 2.0%  |  Gap: {inflation - 2:.1f}pp',
            'color': C['negative'] if inflation > 3.5 else (C['warning'] if inflation > 2 else C['positive']),
        },
        {
            'theme': 'MARKET STRESS', 'icon': '⚡',
            'headline': 'Panic' if vix_val >= 30 else ('Elevated' if vix_val >= 20 else 'Calm'),
            'stat': f'VIX {vix_val:.1f}  |  HY Spread {hy:.2f}%',
            'detail': f"Credit {'wide — stress elevated' if hy >= 6 else ('moderately elevated' if hy >= 4 else 'contained')}",
            'color': C['negative'] if vix_val >= 30 else (C['warning'] if vix_val >= 20 else C['positive']),
        },
    ]

    cards = []
    for ins in insights:
        cards.append(dbc.Col(
            html.Div([
                html.Div([
                    html.Span(ins['icon'] + ' ', style={'fontSize': '12px'}),
                    html.Span(ins['theme'], style={
                        'color': C['subtext'], 'fontSize': '9px',
                        'fontWeight': '700', 'letterSpacing': '0.12em',
                    }),
                ], style={'marginBottom': '10px'}),
                html.Div(ins['headline'], style={
                    'color': ins['color'], 'fontSize': '20px',
                    'fontWeight': '700', 'marginBottom': '5px',
                }),
                html.Div(ins['stat'], style={
                    'color': C['text'], 'fontSize': '11px',
                    'fontFamily': 'monospace', 'marginBottom': '3px',
                }),
                html.Div(ins['detail'], style={'color': C['muted'], 'fontSize': '11px'}),
            ], style={**CARD_STYLE, 'borderTop': f"2px solid {ins['color']}", 'height': '100%'}),
            xs=12, sm=6, lg=3, className='mb-3'
        ))

    return dbc.Row(cards, className='g-3')


SOURCE_COLORS = {
    'reuters': '#FF8000', 'bloomberg': '#6441A5',
    'ft': '#FCD200', 'wsj': '#004990', 'cnbc': '#00B3E3',
}


def _source_badge(source: str) -> html.Span:
    key = source.lower().replace(' ', '').replace('.', '')
    color = SOURCE_COLORS.get(key, C['accent'])
    return html.Span(source.upper()[:6], style={
        'backgroundColor': f'{color}22', 'border': f'1px solid {color}55',
        'color': color, 'fontSize': '9px', 'fontWeight': '700',
        'letterSpacing': '0.06em', 'borderRadius': '3px', 'padding': '1px 5px',
        'marginRight': '8px', 'flexShrink': '0',
    })


def build_news_panel(articles: list) -> html.Div:
    if not articles:
        return html.Div('No news available.', style={'color': C['muted'], 'fontSize': '13px', 'padding': '16px'})

    rows = []
    for i, art in enumerate(articles[:10]):
        title  = art.get('title', 'Untitled')
        url    = art.get('url', '#')
        source = art.get('source', 'Unknown')
        ts     = art.get('published_utc', '')
        try:
            dt     = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            ts_fmt = dt.strftime('%b %d  %H:%M')
        except Exception:
            ts_fmt = ts[:10] if ts else ''

        rows.append(html.Div([
            html.Span(f'{i+1:02d}', style={
                'color': C['muted'], 'fontSize': '10px', 'fontFamily': 'monospace',
                'minWidth': '22px', 'flexShrink': '0', 'paddingTop': '1px',
            }),
            _source_badge(source),
            html.A(title, href=url, target='_blank', style={
                'color': C['text'], 'fontSize': '13px',
                'textDecoration': 'none', 'flex': '1', 'lineHeight': '1.4',
            }),
            html.Span(ts_fmt, style={
                'color': C['muted'], 'fontSize': '10px', 'fontFamily': 'monospace',
                'marginLeft': '12px', 'flexShrink': '0', 'whiteSpace': 'nowrap',
            }),
        ], style={
            'display': 'flex', 'alignItems': 'flex-start', 'padding': '10px 0',
            'borderBottom': f"1px solid {C['border']}" if i < len(articles) - 1 else 'none',
        }, className='news-row'))

    return html.Div(rows, style={**CARD_STYLE})


def build_footer() -> html.Div:
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    return html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col(html.Span([
                    'Data: ',
                    html.A('FRED', href='https://fred.stlouisfed.org', target='_blank',
                           style={'color': C['accent'], 'textDecoration': 'none'}),
                    ' · ',
                    html.A('Polygon.io', href='https://polygon.io', target='_blank',
                           style={'color': C['accent'], 'textDecoration': 'none'}),
                    ' · ',
                    html.A('yfinance', href='https://github.com/ranaroussi/yfinance', target='_blank',
                           style={'color': C['accent'], 'textDecoration': 'none'}),
                ], style={'color': C['subtext'], 'fontSize': '11px'}), width='auto'),
                dbc.Col(html.Span(f'Generated {now_str}', style={
                    'color': C['muted'], 'fontSize': '11px', 'fontFamily': 'monospace',
                }), className='d-flex justify-content-end'),
            ], justify='between', align='center'),
        ], fluid=True),
    ], style={
        'borderTop': f"1px solid {C['border']}",
        'padding': '12px 0', 'marginTop': '40px',
        'backgroundColor': C['surface'],
    })
