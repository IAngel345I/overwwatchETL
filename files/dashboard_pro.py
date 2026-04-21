# -*- coding: utf-8 -*-
"""
Overwatch 2 BI — Dashboard Profesional v3 (Tema Oficial OW2)
Instalar: pip install dash dash-bootstrap-components plotly psycopg2-binary pandas numpy
Correr:   python dashboard_pro.py
Abrir:    http://127.0.0.1:8050
"""

import psycopg2
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import warnings
warnings.filterwarnings('ignore')

# ─── CONEXION ────────────────────────────────────────────────
DB = dict(host="localhost", port=5432, database="overwatch2", user="postgres", password="planta40")

def query(sql):
    conn = psycopg2.connect(**DB)
    try:
        return pd.read_sql(sql, conn)
    finally:
        conn.close()

df = query("""
    SELECT h.nombre_heroe, h.rol, c.plataforma, c.modo_juego,
           e.region, e.mapa, f.win_rate, f.pick_rate, t.fecha, t.dia_semana
    FROM public.fact_hero_rates f
    JOIN public.dim_heroe     h ON h.id_heroe     = f.id_heroe
    JOIN public.dim_contexto  c ON c.id_contexto  = f.id_contexto
    JOIN public.dim_escenario e ON e.id_escenario = f.id_escenario
    JOIN public.dim_tiempo    t ON t.id_tiempo    = f.id_tiempo
""")
df['fecha'] = pd.to_datetime(df['fecha'])
df['es_finde'] = df['dia_semana'].isin(['Saturday','Sunday','Sabado','Domingo'])

heroes  = sorted(df['nombre_heroe'].unique())
roles   = sorted(df['rol'].dropna().unique())
plats   = sorted(df['plataforma'].unique())
regions = sorted(df['region'].unique())
mapas   = sorted(df['mapa'].unique())

# ─── PALETA OFICIAL OVERWATCH 2 ──────────────────────────────
C = {
    # Fondos oscuros del juego
    'bg':        '#09090f',
    'bg2':       '#0d0d17',
    'surface':   '#11111e',
    'card':      '#141421',
    'card2':     '#1a1a2e',
    'panel':     '#0f0f1c',

    # OW2 Orange — color principal del logo y UI
    'ow_orange':  '#f99e1a',
    'ow_orange2': '#e8860a',
    'ow_orange3': '#ffc444',   # highlight/brillo

    # OW2 Azul/Blanco UI
    'ow_blue':    '#4db8ff',
    'ow_blue2':   '#2196f3',
    'ow_cyan':    '#00e5ff',

    # Texto
    'text':       '#ffffff',
    'text2':      '#c8d0e8',
    'sub':        '#6b7a9f',
    'muted':      '#3d4a6a',

    # Roles (colores exactos OW2)
    'tank':       '#3fa7d6',   # azul tank OW2
    'damage':     '#e05c5c',   # rojo damage OW2
    'support':    '#5cb85c',   # verde support OW2

    # Estado
    'win':        '#00e676',
    'lose':       '#ff5252',
    'gold':       '#ffd54f',

    # Bordes con naranja OW2
    'border':     '#f99e1a20',
    'border2':    '#f99e1a55',
}

# ─── FUENTES Y ESTILOS BASE ──────────────────────────────────
FONT_HERO  = "'Tungsten', 'Barlow Condensed', sans-serif"   # el font del juego
FONT_TITLE = "'Barlow Condensed', sans-serif"
FONT_BODY  = "'Barlow Semi Condensed', 'Barlow', sans-serif"

PLOT_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color=C['text2'], family=FONT_BODY, size=12),
    margin=dict(l=10, r=10, t=36, b=10),
    xaxis=dict(gridcolor='rgba(249,158,26,0.08)', zeroline=False, showline=False, tickfont=dict(color=C['sub'])),
    yaxis=dict(gridcolor='rgba(249,158,26,0.08)', zeroline=False, showline=False, tickfont=dict(color=C['sub'])),
    legend=dict(bgcolor='rgba(0,0,0,0)', bordercolor='rgba(0,0,0,0)', font=dict(color=C['text2'])),
)

COLOR_MAP = {'tank': C['tank'], 'damage': C['damage'], 'support': C['support']}

# Gradiente naranja OW2 para colorscales
OW_SCALE = [
    [0.0,  '#09090f'],
    [0.25, '#1a1a2e'],
    [0.5,  '#2196f3'],
    [0.75, '#f99e1a'],
    [1.0,  '#ffc444'],
]

def card(border_color=None, glow_color=None):
    bc = border_color or C['border2']
    gc = glow_color or 'rgba(249,158,26,0.08)'
    return {
        'background': f"linear-gradient(160deg, {C['card']} 0%, {C['card2']} 100%)",
        'border': f"1px solid {bc}",
        'borderRadius': '4px',
        'padding': '20px',
        'boxShadow': f"0 0 0 0 transparent, 0 8px 32px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.03)",
        'height': '100%',
        'position': 'relative',
        'overflow': 'hidden',
    }

CARD_BASE  = card()
CARD_OW    = card(C['ow_orange']+'66', 'rgba(249,158,26,0.15)')
CARD_BLUE  = card(C['ow_blue']+'44',   'rgba(77,184,255,0.10)')
CARD_GREEN = card(C['win']+'44',       'rgba(0,230,118,0.08)')

DD = {
    'backgroundColor': C['surface'],
    'color': C['text2'],
    'border': f"1px solid {C['border2']}",
    'borderRadius': '3px',
    'fontSize': '13px',
}

# ─── CSS INYECTADO ───────────────────────────────────────────
GLOBAL_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700;800;900&family=Barlow+Semi+Condensed:wght@300;400;500;600&family=Barlow:wght@400;500&display=swap');

* { box-sizing: border-box; }

body {
    background: #09090f !important;
    margin: 0;
    padding: 0;
}

/* Scrollbar OW2 style */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #09090f; }
::-webkit-scrollbar-thumb { background: #f99e1a55; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #f99e1a; }

/* DatePicker override */
.DateInput_input { background: #11111e !important; color: #c8d0e8 !important; border: none !important; font-size: 13px !important; }
.DateRangePickerInput { background: #11111e !important; border: 1px solid #f99e1a55 !important; border-radius: 3px !important; }
.DateRangePickerInput__withBorder { border-radius: 3px !important; }
.DayPicker { background: #11111e !important; }
.CalendarDay__default { background: #11111e !important; color: #c8d0e8 !important; border-color: #1a1a2e !important; }
.CalendarDay__selected { background: #f99e1a !important; color: #09090f !important; }
.CalendarMonth { background: #0d0d17 !important; }
.CalendarMonthGrid { background: #0d0d17 !important; }

/* Dropdown overrides */
.Select-control { background: #11111e !important; border-color: #f99e1a55 !important; }
.Select-menu-outer { background: #11111e !important; border-color: #f99e1a55 !important; }
.VirtualizedSelectOption { background: #11111e !important; color: #c8d0e8 !important; }
.VirtualizedSelectFocusedOption { background: #1a1a2e !important; }

/* Pulse animation para el dot LIVE */
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); box-shadow: 0 0 0 0 #00e67666; }
  50% { opacity: 0.8; transform: scale(1.2); box-shadow: 0 0 0 6px transparent; }
}
.live-dot { animation: pulse 2s ease-in-out infinite; }

/* Card hover subtle glow */
@keyframes borderGlow {
  0%, 100% { border-color: rgba(249,158,26,0.3); }
  50% { border-color: rgba(249,158,26,0.6); }
}

/* Diagonal stripe pattern sutil como OW2 */
.ow-pattern {
  background-image: repeating-linear-gradient(
    -55deg,
    transparent,
    transparent 8px,
    rgba(249,158,26,0.015) 8px,
    rgba(249,158,26,0.015) 9px
  );
}
"""

# ─── APP ─────────────────────────────────────────────────────
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Overwatch 2 | Hero Analytics",
    suppress_callback_exceptions=True,
)

app.index_string = f'''
<!DOCTYPE html>
<html>
<head>
{{%metas%}}
<title>{{%title%}}</title>
{{%favicon%}}
{{%css%}}
<style>{GLOBAL_CSS}</style>
</head>
<body>
{{%app_entry%}}
<footer>{{%config%}}{{%scripts%}}{{%renderer%}}</footer>
</body>
</html>
'''

# ─── COMPONENTES ─────────────────────────────────────────────
def ow_label(text):
    return html.Div(text, style={
        'color': C['sub'], 'fontSize': '10px', 'letterSpacing': '2px',
        'textTransform': 'uppercase', 'marginBottom': '6px',
        'display': 'block', 'fontFamily': FONT_BODY, 'fontWeight': '600',
    })

def kpi_card_cmp(icon, label, vid, accent=C['ow_orange']):
    return html.Div(className='ow-pattern', style={
        'background': f"linear-gradient(160deg, {C['card']} 0%, {C['card2']} 100%)",
        'border': f"1px solid {accent}44",
        'borderBottom': f"3px solid {accent}",
        'borderRadius': '4px',
        'padding': '18px 16px 14px',
        'textAlign': 'center',
        'position': 'relative',
        'overflow': 'hidden',
        'boxShadow': f"0 4px 20px rgba(0,0,0,0.5), 0 0 0 0 transparent",
        'height': '100%',
    }, children=[
        # Corner accent
        html.Div(style={
            'position': 'absolute', 'top': 0, 'right': 0,
            'width': '0', 'height': '0',
            'borderStyle': 'solid',
            'borderWidth': '0 28px 28px 0',
            'borderColor': f"transparent {accent}33 transparent transparent",
        }),
        html.Div(icon, style={'fontSize': '22px', 'marginBottom': '6px', 'lineHeight': '1'}),
        html.Div(label, style={
            'color': C['sub'], 'fontSize': '9px', 'letterSpacing': '2.5px',
            'textTransform': 'uppercase', 'marginBottom': '6px',
            'fontFamily': FONT_BODY, 'fontWeight': '600',
        }),
        html.Div(id=vid, style={
            'color': accent, 'fontSize': '26px', 'fontWeight': '900',
            'fontFamily': FONT_TITLE, 'letterSpacing': '0px', 'lineHeight': '1',
        }),
    ])

def section_header(text, icon="", accent=C['ow_orange']):
    return html.Div(style={
        'display': 'flex', 'alignItems': 'center',
        'marginBottom': '16px', 'gap': '10px',
    }, children=[
        # Barra vertical izquierda — estilo OW2
        html.Div(style={
            'width': '4px', 'height': '18px', 'borderRadius': '2px',
            'background': f"linear-gradient(180deg, {accent}, {accent}66)",
            'flexShrink': 0,
        }),
        html.Span(icon, style={'fontSize': '14px'}),
        html.H3(text, style={
            'margin': 0, 'color': C['text'], 'fontFamily': FONT_TITLE,
            'fontSize': '14px', 'letterSpacing': '3px',
            'textTransform': 'uppercase', 'fontWeight': '800',
        }),
        html.Div(style={
            'flex': 1, 'height': '1px',
            'background': f"linear-gradient(to right, {accent}55, transparent)",
        }),
        # Tag pequeño
        html.Div(text[:4].upper(), style={
            'backgroundColor': f"{accent}22",
            'color': accent, 'padding': '2px 8px',
            'borderRadius': '2px', 'fontSize': '9px',
            'fontWeight': '700', 'letterSpacing': '2px',
            'fontFamily': FONT_BODY, 'border': f"1px solid {accent}44",
        }),
    ])

# ─── LAYOUT ──────────────────────────────────────────────────
app.layout = html.Div(style={
    'backgroundColor': C['bg'],
    'minHeight': '100vh',
    'fontFamily': FONT_BODY,
    'color': C['text'],
}, children=[

    # ══ HEADER ════════════════════════════════════════════════
    html.Div(style={
        'background': f"linear-gradient(180deg, #0f0f1c 0%, {C['bg']} 100%)",
        'borderBottom': f"2px solid {C['ow_orange']}",
        'padding': '0 32px',
        'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between',
        'height': '76px',
        'boxShadow': f"0 2px 40px rgba(249,158,26,0.25), 0 0 80px rgba(249,158,26,0.05)",
        'position': 'relative',
        'zIndex': 100,
    }, children=[

        # Diagonal background accent
        html.Div(className='ow-pattern', style={
            'position': 'absolute', 'inset': 0, 'pointerEvents': 'none', 'zIndex': 0,
        }),
        html.Div(style={
            'position': 'absolute', 'right': 0, 'top': 0, 'bottom': 0, 'width': '35%',
            'background': f"linear-gradient(to left, {C['ow_orange']}08, transparent)",
            'zIndex': 0,
        }),

        # Logo + Título
        html.Div(style={'display': 'flex', 'alignItems': 'center', 'gap': '16px', 'zIndex': 1}, children=[
            # Ícono circular estilo OW2
            html.Div(style={
                'width': '52px', 'height': '52px',
                'background': f"linear-gradient(135deg, {C['ow_orange']} 0%, {C['ow_orange2']} 60%, {C['ow_orange3']} 100%)",
                'borderRadius': '50%',
                'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
                'fontSize': '26px',
                'boxShadow': f"0 0 0 2px {C['ow_orange']}44, 0 0 24px {C['ow_orange']}66",
                'flexShrink': 0,
            }, children="⚔"),

            # Texto
            html.Div([
                html.Div(style={'display': 'flex', 'alignItems': 'baseline', 'gap': '6px'}, children=[
                    html.Span("OVERWATCH", style={
                        'fontFamily': FONT_TITLE, 'fontSize': '30px', 'fontWeight': '900',
                        'color': C['text'], 'letterSpacing': '2px', 'lineHeight': '1',
                    }),
                    html.Span("2", style={
                        'fontFamily': FONT_TITLE, 'fontSize': '30px', 'fontWeight': '900',
                        'color': C['ow_orange'], 'letterSpacing': '2px', 'lineHeight': '1',
                    }),
                ]),
                html.Div(style={'display': 'flex', 'alignItems': 'center', 'gap': '8px', 'marginTop': '2px'}, children=[
                    html.Div(style={'width': '24px', 'height': '1px', 'backgroundColor': C['ow_orange']}),
                    html.Span("HERO ANALYTICS DASHBOARD", style={
                        'fontSize': '9px', 'color': C['sub'],
                        'letterSpacing': '4px', 'fontFamily': FONT_BODY,
                    }),
                    html.Div(style={'width': '24px', 'height': '1px', 'backgroundColor': C['ow_orange']}),
                ]),
            ]),
        ]),

        # Badges derecha
        html.Div(style={'display': 'flex', 'gap': '10px', 'alignItems': 'center', 'zIndex': 1}, children=[
            # LIVE
            html.Div(style={'display': 'flex', 'alignItems': 'center', 'gap': '6px',
                            'padding': '6px 12px', 'border': f"1px solid {C['win']}44",
                            'borderRadius': '3px', 'backgroundColor': f"{C['win']}11"}, children=[
                html.Div(className='live-dot', style={
                    'width': '7px', 'height': '7px', 'borderRadius': '50%',
                    'backgroundColor': C['win'],
                }),
                html.Span("LIVE", style={
                    'color': C['win'], 'fontSize': '10px',
                    'fontWeight': '700', 'letterSpacing': '2px', 'fontFamily': FONT_BODY,
                }),
            ]),
            html.Div(style={
                'background': f"linear-gradient(135deg, {C['ow_orange']}, {C['ow_orange2']})",
                'color': C['bg'], 'padding': '6px 14px', 'borderRadius': '3px',
                'fontSize': '11px', 'fontWeight': '800', 'letterSpacing': '2px',
                'fontFamily': FONT_TITLE,
            }, children="SEASON 15"),
            html.Div(style={
                'border': f"1px solid {C['ow_blue']}66", 'color': C['ow_blue'],
                'padding': '6px 14px', 'borderRadius': '3px',
                'fontSize': '11px', 'letterSpacing': '2px', 'fontFamily': FONT_TITLE,
                'fontWeight': '700',
            }, children="COMPETITIVE"),
            html.Div(style={
                'border': f"1px solid {C['sub']}44", 'color': C['sub'],
                'padding': '6px 14px', 'borderRadius': '3px',
                'fontSize': '11px', 'letterSpacing': '2px', 'fontFamily': FONT_TITLE,
            }, children="ROLE QUEUE"),
        ]),
    ]),

    # ══ BODY ══════════════════════════════════════════════════
    html.Div(style={'padding': '20px 32px'}, children=[

        # ── KPIs ──────────────────────────────────────────────
        dbc.Row(style={'marginBottom': '20px', 'gap': '0'}, children=[
            dbc.Col(kpi_card_cmp("📊", "Registros Totales", "kpi-total",  C['ow_orange']),  width=2),
            dbc.Col(kpi_card_cmp("🦸", "Héroes Activos",   "kpi-heroes", C['ow_blue']),    width=2),
            dbc.Col(kpi_card_cmp("🏆", "Win Rate Prom.",   "kpi-wr",     C['win']),         width=2),
            dbc.Col(kpi_card_cmp("🎯", "Pick Rate Prom.",  "kpi-pr",     C['ow_orange3']), width=2),
            dbc.Col(kpi_card_cmp("⭐", "Top Héroe Hoy",    "kpi-top",    C['gold']),        width=2),
            dbc.Col(kpi_card_cmp("📅", "Días de Datos",    "kpi-dias",   C['ow_cyan']),     width=2),
        ]),

        # ── FILTROS ───────────────────────────────────────────
        html.Div(className='ow-pattern', style={
            **CARD_OW, 'marginBottom': '20px',
        }, children=[
            section_header("Filtros Globales", "🔍", C['ow_orange']),
            dbc.Row([
                dbc.Col([ow_label("Plataforma"),
                    dcc.Dropdown(id='f-plat', options=[{'label':p,'value':p} for p in plats],
                                 placeholder="Todas", style=DD, clearable=True)], width=2),
                dbc.Col([ow_label("Región"),
                    dcc.Dropdown(id='f-region', options=[{'label':r,'value':r} for r in regions],
                                 placeholder="Todas", style=DD, clearable=True)], width=2),
                dbc.Col([ow_label("Rol"),
                    dcc.Dropdown(id='f-rol', options=[{'label':r.title(),'value':r} for r in roles],
                                 placeholder="Todos", style=DD, clearable=True)], width=2),
                dbc.Col([ow_label("Mapa"),
                    dcc.Dropdown(id='f-mapa', options=[{'label':m,'value':m} for m in mapas],
                                 placeholder="Todos", style=DD, clearable=True)], width=3),
                dbc.Col([ow_label("Rango de Fechas"),
                    dcc.DatePickerRange(id='f-fecha',
                        min_date_allowed=df['fecha'].min(), max_date_allowed=df['fecha'].max(),
                        start_date=df['fecha'].min(), end_date=df['fecha'].max())], width=3),
            ]),
        ]),

        # ── FILA 1: Top 10 + Donut ────────────────────────────
        dbc.Row(style={'marginBottom': '16px'}, children=[
            dbc.Col([html.Div(className='ow-pattern', style=CARD_OW, children=[
                section_header("Top 10 Héroes por Win Rate", "🏆", C['ow_orange']),
                dcc.Graph(id='g-top10', config={'displayModeBar':False}, style={'height':'360px'}),
            ])], width=7),
            dbc.Col([html.Div(className='ow-pattern', style=CARD_BLUE, children=[
                section_header("Distribución por Rol", "🎯", C['ow_blue']),
                dcc.Graph(id='g-rol', config={'displayModeBar':False}, style={'height':'360px'}),
            ])], width=5),
        ]),

        # ── FILA 2: Evolución + Tendencia ─────────────────────
        dbc.Row(style={'marginBottom': '16px'}, children=[
            dbc.Col([html.Div(className='ow-pattern', style=CARD_OW, children=[
                section_header("Evolución Diaria + Predicción 7 días", "📈", C['ow_orange']),
                dcc.Graph(id='g-evolucion', config={'displayModeBar':False}, style={'height':'320px'}),
            ])], width=8),
            dbc.Col([html.Div(className='ow-pattern', style=CARD_GREEN, children=[
                section_header("Ascenso vs Declive", "📊", C['win']),
                dcc.Graph(id='g-tendencia', config={'displayModeBar':False}, style={'height':'320px'}),
            ])], width=4),
        ]),

        # ── FILA 3: Heatmap ───────────────────────────────────
        dbc.Row(style={'marginBottom': '16px'}, children=[
            dbc.Col([html.Div(className='ow-pattern', style=CARD_OW, children=[
                section_header("Heatmap — Win Rate por Héroe vs Mapa", "🔥", C['ow_orange']),
                dcc.Graph(id='g-heatmap', config={'displayModeBar':False}, style={'height':'440px'}),
            ])], width=12),
        ]),

        # ── FILA 4: Radar + Boxplot ───────────────────────────
        dbc.Row(style={'marginBottom': '16px'}, children=[
            dbc.Col([html.Div(className='ow-pattern', style=CARD_BLUE, children=[
                section_header("Radar — Comparar 2 Héroes", "🕹️", C['ow_blue']),
                dbc.Row([
                    dbc.Col([dcc.Dropdown(id='radar-h1',
                        options=[{'label':h,'value':h} for h in heroes],
                        value=heroes[0] if heroes else None, style=DD)], width=6),
                    dbc.Col([dcc.Dropdown(id='radar-h2',
                        options=[{'label':h,'value':h} for h in heroes],
                        value=heroes[1] if len(heroes)>1 else None, style=DD)], width=6),
                ], style={'marginBottom':'14px'}),
                dcc.Graph(id='g-radar', config={'displayModeBar':False}, style={'height':'320px'}),
            ])], width=5),
            dbc.Col([html.Div(className='ow-pattern', style=CARD_BLUE, children=[
                section_header("Boxplot Win Rate por Rol", "📦", C['ow_blue']),
                dcc.Graph(id='g-boxplot', config={'displayModeBar':False}, style={'height':'370px'}),
            ])], width=7),
        ]),

        # ── FILA 5: Finde + Top Región ────────────────────────
        dbc.Row(style={'marginBottom': '16px'}, children=[
            dbc.Col([html.Div(className='ow-pattern', style=CARD_OW, children=[
                section_header("Fin de Semana vs Entre Semana", "📅", C['ow_orange']),
                dcc.Graph(id='g-finde', config={'displayModeBar':False}, style={'height':'320px'}),
            ])], width=6),
            dbc.Col([html.Div(className='ow-pattern', style=CARD_GREEN, children=[
                section_header("Top Héroe por Región", "🌎", C['win']),
                dcc.Graph(id='g-region-top', config={'displayModeBar':False}, style={'height':'320px'}),
            ])], width=6),
        ]),

        # ── FILA 6: Tanks Heatmap + Supports ─────────────────
        dbc.Row(style={'marginBottom': '16px'}, children=[
            dbc.Col([html.Div(className='ow-pattern', style=CARD_BLUE, children=[
                section_header("Tanks — PC vs Console", "🛡️", C['tank']),
                dcc.Graph(id='g-tanks', config={'displayModeBar':False}, style={'height':'340px'}),
            ])], width=6),
            dbc.Col([html.Div(className='ow-pattern', style=CARD_GREEN, children=[
                section_header("Supports Dominantes por Región", "💚", C['support']),
                dcc.Graph(id='g-supports', config={'displayModeBar':False}, style={'height':'340px'}),
            ])], width=6),
        ]),

        # ── FILA 7: Consistencia + Scatter ────────────────────
        dbc.Row(style={'marginBottom': '16px'}, children=[
            dbc.Col([html.Div(className='ow-pattern', style=CARD_OW, children=[
                section_header("Héroes más Consistentes", "🎖️", C['ow_orange']),
                dcc.Graph(id='g-consistencia', config={'displayModeBar':False}, style={'height':'320px'}),
            ])], width=5),
            dbc.Col([html.Div(className='ow-pattern', style=CARD_BLUE, children=[
                section_header("Win Rate vs Pick Rate — Scatter", "📊", C['ow_cyan']),
                dcc.Graph(id='g-scatter', config={'displayModeBar':False}, style={'height':'320px'}),
            ])], width=7),
        ]),

        # ── FILA 8: PC/Console + Región + Mapa ───────────────
        dbc.Row(style={'marginBottom': '16px'}, children=[
            dbc.Col([html.Div(className='ow-pattern', style=CARD_OW, children=[
                section_header("PC vs Console", "🖥️", C['ow_orange']),
                dcc.Graph(id='g-plat', config={'displayModeBar':False}, style={'height':'300px'}),
            ])], width=4),
            dbc.Col([html.Div(className='ow-pattern', style=CARD_BLUE, children=[
                section_header("Pick Rate por Región", "🌎", C['ow_blue']),
                dcc.Graph(id='g-region', config={'displayModeBar':False}, style={'height':'300px'}),
            ])], width=4),
            dbc.Col([html.Div(className='ow-pattern', style=CARD_GREEN, children=[
                section_header("Win Rate por Mapa", "🗺️", C['win']),
                dcc.Graph(id='g-mapa', config={'displayModeBar':False}, style={'height':'300px'}),
            ])], width=4),
        ]),

        # ── TABLA ─────────────────────────────────────────────
        html.Div(className='ow-pattern', style=CARD_OW, children=[
            section_header("Ranking Detallado — Top 20", "📋", C['ow_orange']),
            html.Div(id='tabla'),
        ]),
    ]),

    # ── FOOTER ────────────────────────────────────────────────
    html.Div(style={
        'borderTop': f"2px solid {C['ow_orange']}55",
        'background': f"linear-gradient(180deg, {C['bg']} 0%, {C['surface']} 100%)",
        'padding': '16px 32px',
        'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center',
    }, children=[
        html.Div(style={'display': 'flex', 'alignItems': 'center', 'gap': '8px'}, children=[
            html.Span("⚔", style={'fontSize': '16px'}),
            html.Span("OVERWATCH 2", style={'color': C['ow_orange'], 'fontWeight': '900',
                                             'fontFamily': FONT_TITLE, 'fontSize': '13px', 'letterSpacing': '2px'}),
            html.Span(" HERO ANALYTICS", style={'color': C['sub'], 'fontSize': '11px', 'letterSpacing': '2px'}),
        ]),
        html.Span("PYTHON + DASH + POSTGRESQL", style={
            'color': C['muted'], 'fontSize': '10px', 'letterSpacing': '3px', 'fontFamily': FONT_BODY,
        }),
        html.Div(style={'display': 'flex', 'gap': '6px'}, children=[
            html.Div(style={'width': '8px', 'height': '8px', 'borderRadius': '50%', 'backgroundColor': C['tank']}),
            html.Div(style={'width': '8px', 'height': '8px', 'borderRadius': '50%', 'backgroundColor': C['damage']}),
            html.Div(style={'width': '8px', 'height': '8px', 'borderRadius': '50%', 'backgroundColor': C['support']}),
        ]),
    ]),
])

# ─── HELPERS ─────────────────────────────────────────────────
def fil(plat, region, rol, mapa, fi, ff):
    d = df.copy()
    if plat:   d = d[d['plataforma'] == plat]
    if region: d = d[d['region'] == region]
    if rol:    d = d[d['rol'] == rol]
    if mapa:   d = d[d['mapa'] == mapa]
    if fi:     d = d[d['fecha'] >= pd.to_datetime(fi)]
    if ff:     d = d[d['fecha'] <= pd.to_datetime(ff)]
    return d

INPUTS = [
    Input('f-plat','value'), Input('f-region','value'), Input('f-rol','value'),
    Input('f-mapa','value'), Input('f-fecha','start_date'), Input('f-fecha','end_date'),
]

# ─── CALLBACKS ───────────────────────────────────────────────
@app.callback(
    Output('kpi-total','children'), Output('kpi-heroes','children'),
    Output('kpi-wr','children'),    Output('kpi-pr','children'),
    Output('kpi-top','children'),   Output('kpi-dias','children'),
    *INPUTS)
def kpis(plat, region, rol, mapa, fi, ff):
    d = fil(plat, region, rol, mapa, fi, ff)
    hoy = d['fecha'].max()
    d_hoy = d[d['fecha'] == hoy]
    top = (d_hoy.groupby('nombre_heroe')['win_rate'].mean().idxmax() if len(d_hoy)
           else d.groupby('nombre_heroe')['win_rate'].mean().idxmax() if len(d) else "N/A")
    return (f"{len(d):,}", str(d['nombre_heroe'].nunique()),
            f"{d['win_rate'].mean():.1f}%", f"{d['pick_rate'].mean():.1f}%",
            top, str(d['fecha'].nunique()))

@app.callback(Output('g-top10','figure'), *INPUTS)
def top10(plat, region, rol, mapa, fi, ff):
    d = fil(plat, region, rol, mapa, fi, ff)
    agg = d.groupby(['nombre_heroe','rol'])['win_rate'].mean().reset_index().nlargest(10,'win_rate')
    fig = px.bar(agg, x='win_rate', y='nombre_heroe', color='rol',
                 color_discrete_map=COLOR_MAP, orientation='h',
                 text=agg['win_rate'].round(1).astype(str)+'%')
    fig.update_traces(textposition='outside', textfont=dict(color=C['text2'], size=11))
    fig.update_layout(**PLOT_LAYOUT, xaxis_title="Win Rate %", yaxis_title="")
    return fig

@app.callback(Output('g-rol','figure'), *INPUTS)
def rol_chart(plat, region, rol, mapa, fi, ff):
    d = fil(plat, region, rol, mapa, fi, ff)
    agg = d.groupby('rol')['win_rate'].mean().reset_index().dropna()
    fig = go.Figure(go.Pie(
        labels=agg['rol'], values=agg['win_rate'].round(2), hole=0.58,
        marker=dict(colors=[COLOR_MAP.get(r, C['sub']) for r in agg['rol']],
                    line=dict(color=C['bg'], width=5)),
        textinfo='label+percent',
        textfont=dict(color=C['text'], size=13, family=FONT_TITLE),
    ))
    fig.update_layout(**PLOT_LAYOUT)
    return fig

@app.callback(Output('g-evolucion','figure'), *INPUTS)
def evolucion(plat, region, rol, mapa, fi, ff):
    d = fil(plat, region, rol, mapa, fi, ff)
    top5 = d.groupby('nombre_heroe')['win_rate'].mean().nlargest(5).index
    agg = d[d['nombre_heroe'].isin(top5)].groupby(['fecha','nombre_heroe'])['win_rate'].mean().reset_index()
    colors = [C['ow_orange'], C['ow_blue'], C['win'], C['tank'], C['support']]
    fig = px.line(agg, x='fecha', y='win_rate', color='nombre_heroe', markers=True,
                  color_discrete_sequence=colors)
    fig.update_traces(line_width=2.5, marker_size=6)
    for i, heroe in enumerate(top5):
        sub = agg[agg['nombre_heroe']==heroe].sort_values('fecha')
        if len(sub) >= 3:
            z = np.polyfit(np.arange(len(sub)), sub['win_rate'], 1)
            fut_dates = pd.date_range(sub['fecha'].max()+pd.Timedelta(days=1), periods=7)
            fut_y = np.poly1d(z)(np.arange(len(sub), len(sub)+7))
            fig.add_scatter(x=fut_dates, y=fut_y, mode='lines',
                line=dict(dash='dot', color=colors[i%len(colors)], width=1.5),
                showlegend=False, opacity=0.5)
    fig.update_layout(**PLOT_LAYOUT, xaxis_title="Fecha", yaxis_title="Win Rate %")
    return fig

@app.callback(Output('g-tendencia','figure'), *INPUTS)
def tendencia(plat, region, rol, mapa, fi, ff):
    d = fil(plat, region, rol, mapa, fi, ff)
    fechas = sorted(d['fecha'].unique())
    if len(fechas) < 2:
        return go.Figure().update_layout(**PLOT_LAYOUT)
    mitad = fechas[len(fechas)//2]
    primera = d[d['fecha']<=mitad].groupby('nombre_heroe')['win_rate'].mean()
    segunda  = d[d['fecha']>mitad].groupby('nombre_heroe')['win_rate'].mean()
    comp = pd.DataFrame({'primera':primera,'segunda':segunda}).dropna()
    comp['cambio'] = comp['segunda'] - comp['primera']
    asc = comp.nlargest(5,'cambio')[['cambio']].reset_index()
    dec = comp.nsmallest(5,'cambio')[['cambio']].reset_index()
    fig = go.Figure()
    fig.add_bar(x=asc['nombre_heroe'], y=asc['cambio'], name='Ascenso', marker_color=C['win'])
    fig.add_bar(x=dec['nombre_heroe'], y=dec['cambio'], name='Declive',  marker_color=C['damage'])
    fig.update_layout(**PLOT_LAYOUT, barmode='group', xaxis_tickangle=-30, yaxis_title="Δ Win Rate %")
    return fig

@app.callback(Output('g-heatmap','figure'), *INPUTS)
def heatmap(plat, region, rol, mapa, fi, ff):
    d = fil(plat, region, rol, mapa, fi, ff)
    top15 = d.groupby('nombre_heroe')['win_rate'].mean().nlargest(15).index
    pivot = d[d['nombre_heroe'].isin(top15)].pivot_table(
        index='nombre_heroe', columns='mapa', values='win_rate', aggfunc='mean').round(1)
    fig = go.Figure(go.Heatmap(
        z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
        colorscale=OW_SCALE,
        text=pivot.values.round(1), texttemplate='%{text}',
        textfont=dict(size=10, color='white'),
        colorbar=dict(title='Win Rate %', tickfont=dict(color=C['text2']),
                      titlefont=dict(color=C['ow_orange'])),
    ))
    fig.update_layout(**PLOT_LAYOUT, xaxis_tickangle=-35)
    return fig

@app.callback(Output('g-radar','figure'),
    Input('radar-h1','value'), Input('radar-h2','value'), *INPUTS)
def radar(h1, h2, plat, region, rol, mapa, fi, ff):
    d = fil(plat, region, rol, mapa, fi, ff)
    regiones_list = sorted(d['region'].unique())
    categories = ['Win Rate','Pick Rate'] + [f'WR {r}' for r in regiones_list]
    fig = go.Figure()
    for heroe, color in [(h1, C['ow_orange']), (h2, C['ow_blue'])]:
        if not heroe: continue
        sub = d[d['nombre_heroe']==heroe]
        vals = [
            min(100, max(0, (sub['win_rate'].mean()-40)/20*100)),
            min(100, max(0, sub['pick_rate'].mean()/25*100)),
        ]
        for reg in regiones_list:
            s = sub[sub['region']==reg]['win_rate'].mean() if len(sub[sub['region']==reg]) else 50
            vals.append(min(100, max(0, (s-40)/20*100)))
        fig.add_trace(go.Scatterpolar(
            r=vals+[vals[0]], theta=categories+[categories[0]],
            fill='toself', name=heroe, line_color=color,
            fillcolor=color+'22', line_width=2.5,
        ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=C['text2'], family=FONT_BODY),
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(visible=True, range=[0,100],
                          gridcolor=C['border2'], color=C['sub'], tickfont=dict(size=9)),
            angularaxis=dict(gridcolor=C['border2'], color=C['text2'],
                           tickfont=dict(size=10, family=FONT_BODY)),
        ),
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color=C['text2'])),
        margin=dict(l=40, r=40, t=20, b=20),
    )
    return fig

@app.callback(Output('g-boxplot','figure'), *INPUTS)
def boxplot(plat, region, rol, mapa, fi, ff):
    d = fil(plat, region, rol, mapa, fi, ff)
    fig = go.Figure()
    for r in roles:
        sub = d[d['rol']==r]['win_rate']
        c = COLOR_MAP.get(r, C['sub'])
        fig.add_trace(go.Box(y=sub, name=r.title(), marker_color=c,
                             boxmean='sd', line_width=2, fillcolor=c+'22'))
    fig.update_layout(**PLOT_LAYOUT, yaxis_title="Win Rate %", showlegend=False)
    return fig

@app.callback(Output('g-finde','figure'), *INPUTS)
def finde(plat, region, rol, mapa, fi, ff):
    d = fil(plat, region, rol, mapa, fi, ff)
    top10h = d.groupby('nombre_heroe')['win_rate'].mean().nlargest(10).index
    d10 = d[d['nombre_heroe'].isin(top10h)].copy()
    d10['periodo'] = d10['es_finde'].map({True:'Fin de Semana', False:'Entre Semana'})
    agg = d10.groupby(['nombre_heroe','periodo'])['win_rate'].mean().reset_index()
    fig = px.bar(agg, x='nombre_heroe', y='win_rate', color='periodo', barmode='group',
                 color_discrete_map={'Fin de Semana': C['ow_orange'], 'Entre Semana': C['ow_blue']})
    fig.update_layout(**PLOT_LAYOUT, xaxis_tickangle=-35, xaxis_title="", yaxis_title="Win Rate %")
    return fig

@app.callback(Output('g-region-top','figure'), *INPUTS)
def region_top(plat, region, rol, mapa, fi, ff):
    d = fil(plat, region, rol, mapa, fi, ff)
    agg = d.groupby(['region','nombre_heroe'])['win_rate'].mean().reset_index()
    top = agg.loc[agg.groupby('region')['win_rate'].idxmax()]
    fig = px.bar(top, x='region', y='win_rate', color='nombre_heroe', text='nombre_heroe',
                 color_discrete_sequence=[C['ow_orange'], C['ow_blue'], C['win']])
    fig.update_traces(textposition='outside', textfont=dict(color=C['text'], size=13, family=FONT_TITLE))
    fig.update_layout(**PLOT_LAYOUT, showlegend=False, yaxis_title="Win Rate %", xaxis_title="")
    return fig

@app.callback(Output('g-tanks','figure'), *INPUTS)
def tanks_heatmap(plat, region, rol, mapa, fi, ff):
    d = fil(None, region, None, mapa, fi, ff)
    tanks = d[d['rol']=='tank']
    pivot = tanks.pivot_table(index='nombre_heroe', columns='plataforma', values='win_rate', aggfunc='mean').round(2)
    fig = go.Figure(go.Heatmap(
        z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
        colorscale=[[0, C['surface']], [0.5, C['ow_blue2']], [1, C['ow_orange']]],
        text=pivot.values.round(1), texttemplate='%{text}%',
        textfont=dict(size=11, color='white'),
        colorbar=dict(title='Win Rate', tickfont=dict(color=C['text2'])),
    ))
    fig.update_layout(**PLOT_LAYOUT)
    return fig

@app.callback(Output('g-supports','figure'), *INPUTS)
def supports(plat, region, rol, mapa, fi, ff):
    d = fil(plat, None, None, mapa, fi, ff)
    sups = d[d['rol']=='support']
    agg = sups.groupby(['region','nombre_heroe'])['win_rate'].mean().reset_index()
    top = agg.groupby('region').apply(lambda x: x.nlargest(3,'win_rate')).reset_index(drop=True)
    fig = px.bar(top, x='nombre_heroe', y='win_rate', color='region', barmode='group',
                 color_discrete_sequence=[C['ow_orange'], C['ow_blue'], C['win']], facet_col='region')
    fig.update_layout(**PLOT_LAYOUT, showlegend=False, yaxis_title="Win Rate %")
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1], font=dict(color=C['text2'])))
    return fig

@app.callback(Output('g-consistencia','figure'), *INPUTS)
def consistencia(plat, region, rol, mapa, fi, ff):
    d = fil(plat, region, rol, mapa, fi, ff)
    std = d.groupby(['nombre_heroe','rol'])['win_rate'].std().reset_index()
    std.columns = ['nombre_heroe','rol','std_wr']
    std = std.dropna().nsmallest(10,'std_wr')
    fig = px.bar(std, x='std_wr', y='nombre_heroe', color='rol', orientation='h',
                 color_discrete_map=COLOR_MAP, text=std['std_wr'].round(2).astype(str))
    fig.update_traces(textposition='outside', textfont=dict(color=C['text2'], size=10))
    fig.update_layout(**PLOT_LAYOUT, xaxis_title="Desviación Estándar", yaxis_title="")
    return fig

@app.callback(Output('g-scatter','figure'), *INPUTS)
def scatter(plat, region, rol, mapa, fi, ff):
    d = fil(plat, region, rol, mapa, fi, ff)
    agg = d.groupby(['nombre_heroe','rol'])[['win_rate','pick_rate']].mean().reset_index()
    fig = px.scatter(agg, x='win_rate', y='pick_rate', color='rol', text='nombre_heroe',
                     size='pick_rate', color_discrete_map=COLOR_MAP)
    fig.update_traces(textposition='top center', textfont_size=10, marker_opacity=0.9)
    fig.add_hline(y=agg['pick_rate'].mean(), line_dash="dot", line_color=C['ow_orange']+'66', opacity=0.6)
    fig.add_vline(x=agg['win_rate'].mean(), line_dash="dot", line_color=C['ow_orange']+'66', opacity=0.6)
    fig.update_layout(**PLOT_LAYOUT, xaxis_title="Win Rate %", yaxis_title="Pick Rate %")
    return fig

@app.callback(Output('g-plat','figure'), *INPUTS)
def plataforma(plat, region, rol, mapa, fi, ff):
    d = fil(None, region, rol, None, fi, ff)
    top8 = d.groupby('nombre_heroe')['win_rate'].mean().nlargest(8).index
    agg = d[d['nombre_heroe'].isin(top8)].groupby(['nombre_heroe','plataforma'])['win_rate'].mean().reset_index()
    fig = px.bar(agg, x='nombre_heroe', y='win_rate', color='plataforma', barmode='group',
                 color_discrete_sequence=[C['ow_orange'], C['ow_blue']])
    fig.update_layout(**PLOT_LAYOUT, xaxis_tickangle=-45, xaxis_title="", yaxis_title="Win Rate %")
    return fig

@app.callback(Output('g-region','figure'), *INPUTS)
def region_chart(plat, region, rol, mapa, fi, ff):
    d = fil(plat, None, rol, None, fi, ff)
    top8 = d.groupby('nombre_heroe')['pick_rate'].mean().nlargest(8).index
    agg = d[d['nombre_heroe'].isin(top8)].groupby(['nombre_heroe','region'])['pick_rate'].mean().reset_index()
    fig = px.bar(agg, x='nombre_heroe', y='pick_rate', color='region', barmode='group',
                 color_discrete_sequence=[C['ow_orange'], C['ow_blue'], C['win']])
    fig.update_layout(**PLOT_LAYOUT, xaxis_tickangle=-45, xaxis_title="", yaxis_title="Pick Rate %")
    return fig

@app.callback(Output('g-mapa','figure'), *INPUTS)
def mapa_chart(plat, region, rol, mapa, fi, ff):
    d = fil(plat, region, rol, None, fi, ff)
    agg = d.groupby('mapa')['win_rate'].mean().reset_index().nlargest(10,'win_rate')
    fig = px.bar(agg, x='win_rate', y='mapa', orientation='h', color='win_rate',
                 color_continuous_scale=[[0, C['surface']], [0.5, C['ow_blue2']], [1, C['ow_orange']]])
    fig.update_layout(**PLOT_LAYOUT, xaxis_title="Win Rate %", yaxis_title="", coloraxis_showscale=False)
    return fig

@app.callback(Output('tabla','children'), *INPUTS)
def tabla(plat, region, rol, mapa, fi, ff):
    d = fil(plat, region, rol, mapa, fi, ff)
    agg = d.groupby(['nombre_heroe','rol','plataforma','region'])[['win_rate','pick_rate']].mean().round(2).reset_index()
    agg = agg.nlargest(20,'win_rate')
    agg.columns = ['Héroe','Rol','Plataforma','Región','Win Rate %','Pick Rate %']
    return dash_table.DataTable(
        data=agg.to_dict('records'),
        columns=[{"name": c, "id": c} for c in agg.columns],
        style_table={'overflowX': 'auto'},
        style_cell={
            'backgroundColor': C['surface'], 'color': C['text2'],
            'border': f"1px solid {C['border']}",
            'padding': '11px 16px', 'fontSize': '13px', 'fontFamily': FONT_BODY,
        },
        style_header={
            'backgroundColor': C['card2'], 'color': C['ow_orange'],
            'fontWeight': '800', 'border': f"1px solid {C['border2']}",
            'letterSpacing': '2px', 'fontSize': '11px', 'fontFamily': FONT_TITLE,
            'textTransform': 'uppercase',
        },
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': C['bg2']},
            {'if': {'filter_query': '{Win Rate %} > 55'},
             'color': C['ow_orange'], 'fontWeight': '700'},
            {'if': {'column_id': 'Héroe', 'filter_query': '{Win Rate %} > 55'},
             'borderLeft': f"3px solid {C['ow_orange']}"},
            {'if': {'column_id': 'Rol', 'filter_query': '{Rol} = tank'},
             'color': C['tank'], 'fontWeight': '600'},
            {'if': {'column_id': 'Rol', 'filter_query': '{Rol} = damage'},
             'color': C['damage'], 'fontWeight': '600'},
            {'if': {'column_id': 'Rol', 'filter_query': '{Rol} = support'},
             'color': C['support'], 'fontWeight': '600'},
        ],
        page_size=10,
        sort_action='native',
    )

if __name__ == '__main__':
    app.run(debug=False, port=8050)
