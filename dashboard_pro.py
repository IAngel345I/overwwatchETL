import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, dash_table, State
import dash_bootstrap_components as dbc
from datetime import datetime
import psycopg2
from urllib.parse import quote

import os

from sqlalchemy import create_engine

# =============================================================
# CONFIGURACION Y DATOS
# =============================================================
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:planta40@localhost:5432/overwatch2")
# Usamos un engine de SQLAlchemy (más eficiente en memoria)
engine = create_engine(DATABASE_URL)

def query(sql):
    try:
        with engine.connect() as conn:
            df = pd.read_sql(sql, conn)
        return df
    except Exception as e:
        print(f"Error DB: {e}")
        return pd.DataFrame()

HERO_IMAGES = {
    "Ana": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/985b06beae46b7ba3ca87d1512d0fc62ca7f206ceca58ef16fc44d43a1cc84ed.png",
    "Anran": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/2c38b41d79a1ce9a08b9ad8eb7edf3ff819bd448af16a5815be8c7fdb7203aa0.png",
    "Ashe": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/4076bbaa2eb52a0bfe612434071e56e7702d5454473dbbea2f9e392a9d997a94.png",
    "Baptiste": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/d4e6f1ca45d9f88fa89260787397f141a6f007b14e5b26698883b6a17bab9680.png",
    "Bastion": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/4ede795c2a681aaccfa72d0c901cba0cb8a2c292fd6a97b2ba9faed161c2d184.png",
    "Brigitte": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/795fba91376d87d441a7f359ae12a3175dfa95825ccc4414cc6b95b129fc4cb0.png",
    "Cassidy": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/9240cd64cc8ef58df9acbf55204ab1b5d8578f743fda5931f0dbccbd75ab841b.png",
    "Domina": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/1161c112292c56c052c0ae711792fcde06e3251b98bc9709e582dd7585b5dcd6.png",
    "Doomfist": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/ff5c54f43ad253c7faeda9c4ed31d42582ea6b19205d197866f3dd0c0aa14c16.png",
    "D.Va": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/df5a5532862d9292634fb3dc0e51a4705aa601de65e5e815513ccc663d84de56.png",
    "Dva": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/df5a5532862d9292634fb3dc0e51a4705aa601de65e5e815513ccc663d84de56.png",
    "Echo": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/d4f2d5b0c2b7e82d61353186c5f23152ccba9d3569b50839aa580dca3e9114ba.png",
    "Emre": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/c51e2f698138861c0e3b6cfab3c3ca9d67fd709be175e7c397aa6f2649712a30.png",
    "Freja": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/811963897c352d9f178bec882d94bd0281074feee7c429c5145b6b8ea8ebe862.png",
    "Genji": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/156b12c20b1aea872c1eeb5bb37a7de1047b2ab30ecefd0663a8925badde1ea8.png",
    "Hanzo": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/78b61c3e806fb26b02b8980fba62189155074fc15bd865b0883268e546030be5.png",
    "Hazard": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/ca48b96dbae6ea7f58ce8a5e73513c8c62b1685bdbf258020fb78bb21a008b5f.png",
    "Illari": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/ce42d1455e03e79f321345fea84b27a8918b5db8bd7ab9b2ca9e569606ede9e4.png",
    "Jetpack Cat": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/03a184cd0de27091e0099ac22635ad9615a8f6997881a5c25cc5f2444764f729.png",
    "Junker Queen": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/06eeecb359f311f43a8f5121d4f9f3a93c565d70b30e94ef543c05596c9a39dc.png",
    "Junkrat": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/7660b9fc6f25f30858fdd8797fe0d52b2306f1e78fef99843f58a274e69af046.png",
    "Juno": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/c0167d251e57b0aa2b1e16c37d87f0e7c77263db9dd0503d77b5f2589bf3e4a0.png",
    "Kiriko": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/408603fe037e8576078eaac5eab2fb251489ced4003b11f5f522776d43d0b83d.png",
    "Lifeweaver": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/3376515cebed0904012e67e956f6d1b9c12e03da642845eeaf787b7e4c7b339d.png",
    "Lucio": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/040bb13f5123ab93faad2f95627ba184608aef4b2469a4d3003859c7087df044.png",
    "Mauga": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/33d39bb439c08975197fc52eff4874716839711b5356c4fdc174f9c24bac1d0e.png",
    "Mei": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/4a55ced3bd597fb08e0fde9dc007f8543ac616ba98ca3db9b0e4d871a8ae17f8.png",
    "Mercy": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/3bfb8bd8ec827e53d870f1238ab73d8aa1f5dbfbcfaaf7f96ffcd35b5c6102ab.png",
    "Mizuki": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/a9733c2367e0cbd70b9316fd2e1e17028653ec56d0051ea6ff098531dc4f99fc.png",
    "Moira": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/f48f8485056d5d00dad195859188d23e50f7126b8b08b5646f46ef1b42f5e1de.png",
    "Orisa": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/a73958a28551f5254f3ab3f97c5f5f8d698a95c0b6a515d1a2b1caac169205a6.png",
    "Pharah": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/60ac2d5de4a6d34644d8872233da402f1436c87f804bb11a21661bb30bf4a51f.png",
    "Ramattra": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/ddef7c9fb8ce4256e8508196b486f81950efe7aaa6cf27fec4668beb4cd15774.png",
    "Reaper": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/dc6ff07ac790c00dc95a40882449617bb6e0e38906b353a630cffe0c815270a9.png",
    "Reinhardt": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/551fbe070c16fdfcc17f7f1de63af22c53e7d2f1340fc2f3172441504527bc4e.png",
    "Roadhog": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/89ddf07e4b619ed96169042e296a1b8856d102746f35add88284b44a9a5a6a03.png",
    "Sierra": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/4bfd3d8b95844231115cb5bf4db03344c71bc3e865189c52403b2dc51438e63a.png",
    "Sigma": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/a4c032fa466c9a6d9c6974747635d7ef910027f91cd58892af0c899db565f92d.png",
    "Sojourn": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/82b8c1b8765dcb9a0ba16e343c3516bf324c771ac81e9878473280216e70a889.png",
    "Soldier: 76": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/c93b5f0a528c40473188f77cc2a267aee7d5b6cf5c9e104105d634b4388674e2.png",
    "Sombra": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/47727b02a16e3bd7b2447d86ae1edf11587bc320b2aecb4f2f16a7ca4ad4e8a0.png",
    "Symmetra": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/ebec57e8bd68b3d4383edfeb34f8f52dd0b94a6467d594c2fee722e8a97c32aa.png",
    "Torbjorn": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/ce17118cedc29b0d2ac1e059666bed36b9531c85079b0b894bb402d12c917ba9.png",
    "Tracer": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/4504f6f15cb3feaa92ecd38e01dcf751cb5abdac2e0bb52d0555727e53277502.png",
    "Vendetta": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/cf8ffb52b6f315546d5e94e9d6defad5a2c570798776956de23f47536f9529da.png",
    "Venture": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/dcab9123f5f55df22e54d4e797de43c71b917e0149dd059a7fd6136f48464cd0.png",
    "Widowmaker": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/6e4702b45f196aaf51555cf57327322721f45458b17f5f0643ed008a88378259.png",
    "Winston": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/46a10db3aa908c590ddc4e7606376a88143d1f1306ecfbea043263040f9529a5.png",
    "Wrecking Ball": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/9ef1d58867136e0b26f928d896000b9dab216118f6e2f59e53f2e975e1e27afa.png",
    "Wuyang": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/4959500b495b35c0908be2abda56b53f2601b2c5cc39a1cfde8df1bffd38d66d.png",
    "Zarya": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/9b6f63cc66ddf9d5e0862173c733cc0d2e574c5c89357798d91b93b2f95a7080.png",
    "Zenyatta": "https://d15f34w2p8l1cc.cloudfront.net/overwatch/7d1546b1541a8afc39353f9337a408d6275a141b0432b7e560ef61579996b0fc.png"
}

def get_hero_img(name):
    if not name: return "https://upload.wikimedia.org/wikipedia/commons/5/55/Overwatch_circle_logo.svg"
    
    # Normalizar nombre del DB (quitar acentos, convertir a string)
    import unicodedata
    import re
    def normalize_str(s):
       s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
       return re.sub(r'[^a-zA-Z0-9]', '', s).lower()
    
    clean_name = normalize_str(str(name))
    
    # Intentar coincidencia exacta en el dict normalizado
    for h_name, url in HERO_IMAGES.items():
        if normalize_str(h_name) == clean_name:
            return url
    
    # Búsqueda difusa
    for h_name, url in HERO_IMAGES.items():
        h_norm = normalize_str(h_name)
        if clean_name in h_norm or h_norm in clean_name:
            return url
            
    return "https://upload.wikimedia.org/wikipedia/commons/5/55/Overwatch_circle_logo.svg"

SQL_RATES = """
    SELECT h.nombre_heroe, h.rol, c.plataforma, c.modo_juego,
           e.region, e.mapa, f.win_rate, f.pick_rate,
           t.fecha, t.dia_semana, t.mes, t.anio
    FROM public.fact_hero_rates f
    JOIN public.dim_heroe     h ON h.id_heroe     = f.id_heroe
    JOIN public.dim_contexto  c ON c.id_contexto  = f.id_contexto
    JOIN public.dim_escenario e ON e.id_escenario = f.id_escenario
    JOIN public.dim_tiempo    t ON t.id_tiempo    = f.id_tiempo
"""

SQL_STATS = """
    SELECT hi.nombre_heroe, r.nombre_rol AS rol, p.nombre_plataforma AS plataforma,
           fs.win_rate, fs.pick_rate, df.fecha, df.dia_semana,
           fs.ranking_position, fs.fuente_tabla
    FROM public.fact_hero_stats fs
    JOIN public.dim_heroe_info hi ON hi.id_heroe     = fs.id_heroe_fk
    JOIN public.dim_rol        r  ON r.id_rol        = fs.id_rol_fk
    JOIN public.dim_plataforma p  ON p.id_plataforma = fs.id_plataforma_fk
    JOIN public.dim_fecha      df ON df.id_fecha     = fs.id_fecha_fk
"""

print("Cargando inteligencia de Overwatch...")
df_rates = query(SQL_RATES)
df_stats = query(SQL_STATS)

if not df_rates.empty:
    df_rates['fuente'] = 'rates'
    df_rates['fecha']  = pd.to_datetime(df_rates['fecha'])
if not df_stats.empty:
    df_stats['fuente'] = 'stats'
    df_stats['fecha']  = pd.to_datetime(df_stats['fecha'])

df = pd.concat([df_rates, df_stats], ignore_index=True, sort=False)
df['win_rate'] = pd.to_numeric(df['win_rate'], errors='coerce').fillna(0)
df['pick_rate'] = pd.to_numeric(df['pick_rate'], errors='coerce').fillna(0)
df['es_finde'] = df['dia_semana'].isin(['Sábado', 'Domingo', 'Saturday', 'Sunday', 6, 7])

# =============================================================
# ESTILOS PREMIUM
# =============================================================
C = {
    'bg': '#08080a',
    'card': 'rgba(25, 25, 35, 0.85)',
    'header': '#000000',
    'border': 'rgba(249, 158, 26, 0.4)',
    'ow_orange': '#f99e1a',
    'ow_blue': '#405275',
    'cyan': '#00c3ff',
    'win': '#00ff88',
    'lose': '#ff4444',
    'text': '#ffffff',
    'sub': '#888899',
    'tank': '#3fa7d6',
    'damage': '#e05c5c',
    'support': '#5cb85c'
}

def glass_card(color=C['border'], padding='25px'):
    return {
        'backgroundColor': C['card'],
        'borderRadius': '12px',
        'padding': padding,
        'marginBottom': '20px',
        'border': f'1px solid {color}',
        'backdropFilter': 'blur(15px)',
        'boxShadow': '0 8px 32px 0 rgba(0, 0, 0, 0.9)',
        'transition': 'all 0.3s ease'
    }

PLOT_LAYOUT = dict(
    template='plotly_dark',
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#e0e0e0', family='Inter, Barlow, sans-serif'),
    margin=dict(l=60, r=40, t=60, b=60),
    hovermode='closest'
)

def section_header(title, icon, color=C['ow_orange']):
    return html.Div(style={'display':'flex', 'alignItems':'center', 'marginBottom':'20px', 'borderLeft':f'4px solid {color}', 'paddingLeft':'15px'}, children=[
        html.Div(icon, style={'fontSize':'20px', 'marginRight':'12px', 'color':color}),
        html.Div(title, style={'fontSize':'14px', 'fontWeight':'900', 'letterSpacing':'2px', 'textTransform':'uppercase', 'color':'#fff'})
    ])

# =============================================================
# APP SETUP
# =============================================================
app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG, "https://fonts.googleapis.com/css2?family=Barlow:wght@300;400;700;900&family=Inter:wght@300;400;700;900&display=swap"])
server = app.server  # NECESARIO PARA EL HOSTING (RENDER/GUNICORN)

app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>OVERWATCH BI | Inteligencia Estratégica</title>
        {%favicon%}
        {%css%}
        <style>
            body { 
                background-color: #08080a; 
                margin: 0; 
                color: #fff;
                font-family: 'Inter', sans-serif;
                overflow-x: hidden; 
            }
            .ow-pattern { 
                background-image: 
                    linear-gradient(rgba(8, 8, 10, 0.93), rgba(8, 8, 10, 0.93)),
                    url('https://images.blz-contentstack.com/v3/assets/blt9c12f249de13ef12/blt6e3f88f8d672808c/6286b5154316930f1469e5d4/ow2-logo-horizontal-white.png');
                background-attachment: fixed;
                background-size: cover;
            }
            
            .Select-control, .Select-menu-outer, .VirtualizedSelectOption {
                background-color: #15151e !important;
                color: white !important;
                border: 1px solid rgba(255,255,255,0.15) !important;
            }
            .Select-menu-outer {
                z-index: 9999 !important;
                border: 1px solid #f99e1a !important;
                box-shadow: 0 10px 30px rgba(0,0,0,0.8) !important;
            }
            .Select-placeholder { color: rgba(255,255,255,0.4) !important; }
            .Select-value-label, .Select-input > input { color: white !important; }
            .Select--single > .Select-control .Select-value { color: white !important; }
            
            .Select--multi .Select-value {
                background-color: #f99e1a !important;
                border: 1px solid #f99e1a !important;
                color: #000 !important;
                border-radius: 4px !important;
                margin: 4px !important;
            }
            .Select--multi .Select-value-label {
                color: #000 !important;
                font-weight: 900 !important;
                text-transform: uppercase !important;
                font-size: 11px !important;
            }
            .Select--multi .Select-value-icon {
                border-right: 1px solid rgba(0,0,0,0.1) !important;
                color: #000 !important;
            }

            .DateRangePickerInput, .DateInput, .DateInput_input {
                background-color: #15151e !important;
                color: white !important;
                border: none !important;
            }
            .DateRangePickerInput {
                border: 1px solid rgba(255,255,255,0.15) !important;
                border-radius: 4px !important;
            }
            .CalendarMonth, .CalendarMonthGrid, .CalendarDay__default, .DayPickerNavigation_button__default {
                background-color: #1a1a25 !important;
                color: white !important;
                border: 1px solid #2d2d3d !important;
            }
            .CalendarDay__selected_span, .CalendarDay__selected {
                background: #f99e1a !important;
                color: black !important;
            }
            .DayPicker_transitionContainer { background-color: #1a1a25 !important; }

            .dash-spreadsheet-container .dash-spreadsheet-inner td { background-color: transparent !important; }
            ::-webkit-scrollbar { width: 8px; }
            ::-webkit-scrollbar-track { background: #08080a; }
            ::-webkit-scrollbar-thumb { background: #f99e1a; border-radius: 10px; }
            .hero-card-hover:hover { transform: translateY(-5px); border-color: #f99e1a !important; box-shadow: 0 0 30px rgba(249, 158, 26, 0.4) !important; }
            .top1-glow { text-shadow: 0 0 25px rgba(249, 158, 26, 1); }
            .hero-img-float { filter: drop-shadow(0 0 20px rgba(249, 158, 26, 0.8)); animation: float 3s ease-in-out infinite; }
            @keyframes float { 0% { transform: translateY(0px); } 50% { transform: translateY(-10px); } 100% { transform: translateY(0px); } }
        </style>
    </head>
    <body class="ow-pattern">
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""

# =============================================================
# LAYOUT COMPONENTS
# =============================================================
def make_chart_container(id, title, icon, width=6, color=C['ow_orange']):
    return dbc.Col(html.Div(style=glass_card(color), className="hero-card-hover", children=[
        section_header(title, icon, color),
        dcc.Graph(id=id, config={'displayModeBar':False}, style={'height':'450px'})
    ]), width=width)

app.layout = html.Div(children=[
    # Header Premium
    html.Div(style={'padding':'25px 60px', 'backgroundColor':'rgba(0,0,0,0.92)', 'borderBottom':f"3px solid {C['ow_orange']}", 'display':'flex', 'justifyContent':'space-between', 'alignItems':'center', 'position':'sticky', 'top':0, 'zIndex':5000, 'backdropFilter':'blur(25px)'}, children=[
        html.Div([
            html.Img(src="https://upload.wikimedia.org/wikipedia/commons/5/55/Overwatch_circle_logo.svg", style={'height':'45px', 'marginRight':'20px'}),
            html.Span("OVERWATCH", style={'fontWeight':'900', 'fontSize':'32px', 'letterSpacing':'8px', 'color':'#fff'}),
            html.Span(" BI", style={'fontWeight':'300', 'fontSize':'32px', 'letterSpacing':'8px', 'color':C['ow_orange']})
        ], style={'display':'flex', 'alignItems':'center'}),
        html.Div([
            html.Div(datetime.now().strftime("%A, %d de %B de %Y").upper(), style={'color':'#fff', 'fontSize':'12px', 'fontWeight':'bold', 'textAlign':'right', 'letterSpacing':'2px'}),
            html.Div("SISTEMA DE INTELIGENCIA ACTIVO", style={'color':C['win'], 'fontSize':'10px', 'letterSpacing':'2px', 'marginTop':'4px', 'textAlign':'right'})
        ])
    ]),

    html.Div(style={'padding':'40px 60px'}, children=[
        
        # SECCIÓN HÉROE DEL DÍA
        html.Div(id='hero-of-the-day-section', style={'marginBottom':'40px'}),

        # FILTROS
        html.Div(style={**glass_card(), 'backgroundColor':'rgba(15, 15, 20, 0.98)', 'position':'relative', 'zIndex':4000}, children=[
            dbc.Row([
                dbc.Col([html.Small("HÉROES OBJETIVO", style={'color':C['ow_orange']}), dcc.Dropdown(id='f-hero', multi=True, placeholder="Cualquier Héroe")], width=4),
                dbc.Col([html.Small("ROLES", style={'color':C['ow_orange']}), dcc.Dropdown(id='f-rol', multi=True, placeholder="Cualquier Rol", options=[{'label':x.upper(),'value':x} for x in df['rol'].dropna().unique()])], width=2),
                dbc.Col([html.Small("PLATAFORMAS", style={'color':C['ow_orange']}), dcc.Dropdown(id='f-plat', multi=True, placeholder="Cualquier Plat.", options=[{'label':x,'value':x} for x in df['plataforma'].dropna().unique()])], width=2),
                dbc.Col([html.Small("RANGO TEMPORAL", style={'color':C['ow_orange']}), dcc.DatePickerRange(id='f-date', start_date=df['fecha'].min(), end_date=df['fecha'].max())], width=4),
            ])
        ]),

        # KPIS
        dbc.Row([
            dbc.Col(html.Div(style=glass_card(C['sub']), children=[
                html.Small("MUESTRAS ANALIZADAS", style={'color':C['sub'], 'letterSpacing':'2px'}),
                html.H2(id='kpi-total', style={'color':'#fff', 'margin':0, 'fontWeight':'900'})
            ]), width=3),
            dbc.Col(html.Div(style=glass_card(C['win']), children=[
                html.Small("TASA DE VICTORIA GLOBAL", style={'color':C['sub'], 'letterSpacing':'2px'}),
                html.H2(id='kpi-wr', style={'color':C['win'], 'margin':0, 'fontWeight':'900'})
            ]), width=2),
            dbc.Col(html.Div(style=glass_card(C['cyan']), children=[
                html.Small("USO PROMEDIO", style={'color':C['sub'], 'letterSpacing':'2px'}),
                html.H2(id='kpi-pr', style={'color':C['cyan'], 'margin':0, 'fontWeight':'900'})
            ]), width=2),
            dbc.Col(html.Div(style=glass_card(C['ow_orange']), children=[
                html.Small("DÍAS REGISTRADOS", style={'color':C['sub'], 'letterSpacing':'2px'}),
                html.H2(id='kpi-days', style={'color':C['ow_orange'], 'margin':0, 'fontWeight':'900'})
            ]), width=2),
            dbc.Col(html.Div(style=glass_card(C['lose']), children=[
                html.Small("META PEAK", style={'color':C['sub'], 'letterSpacing':'2px'}),
                html.H2(id='kpi-top', style={'color':'#fff', 'margin':0, 'fontWeight':'900', 'fontSize':'22px'})
            ]), width=3),
        ], style={'marginBottom':'20px'}),

        # GALERÍA DE HÉROES FILTRADOS
        html.Div(id='hero-gallery-section', style={'marginBottom':'40px'}),

        # 15 GRÁFICOS
        dbc.Row([
            make_chart_container('g-top10', 'Top 10 de Letalidad', '🏆', 7),
            make_chart_container('g-roles', 'Saturación de Roles', '🛡️', 5),
        ]),
        dbc.Row([
            make_chart_container('g-evol', 'Tendencia Temporal por Héroe', '📈', 8),
            make_chart_container('g-delta', 'Variación del Meta', '⚡', 4),
        ]),
        dbc.Row([
            make_chart_container('g-best-map', 'Mejor Héroe por Mapa', '🗺️', 12, C['ow_orange']),
        ]),
        dbc.Row([
            make_chart_container('g-radar', 'ADN por Rol', '🕸️', 6, C['cyan']),
            make_chart_container('g-box', 'Volatilidad de Victoria', '📦', 6, C['win']),
        ]),
        dbc.Row([
            make_chart_container('g-pvp', 'Rendimiento por Plataforma', '🎮', 4),
            make_chart_container('g-mapa', 'Afinidad de Campo de Batalla', '🗺️', 8, C['ow_blue']),
        ]),
        dbc.Row([
            make_chart_container('g-modo', 'Maestría de Objetivos', '🎯', 6),
            make_chart_container('g-region', 'Meta Regional', '🌍', 6),
        ]),
        dbc.Row([
            make_chart_container('g-scatter', 'Matriz de Eficiencia (WR vs PR)', '🎯', 12),
        ]),
        dbc.Row([
            make_chart_container('g-hist', 'Distribución de Victorias', '📊', 4, C['lose']),
            make_chart_container('g-weekend', 'Factor Fin de Semana', '📅', 4),
            make_chart_container('g-bubble', 'Popularidad vs Éxito', '🫧', 4, C['cyan']),
        ]),

        # Tabla Detallada
        html.Div(style=glass_card(), children=[
            section_header("Registro Detallado de Inteligencia", "📠"),
            dash_table.DataTable(
                id='main-table',
                style_table={'overflowX': 'auto'},
                style_cell={'backgroundColor':'rgba(0,0,0,0)', 'color':'#fff', 'borderBottom':'1px solid rgba(255,255,255,0.05)', 'padding':'12px', 'fontSize':'13px', 'textAlign':'left'},
                style_header={'backgroundColor':'rgba(249, 158, 26, 0.1)', 'fontWeight':'900', 'color':C['ow_orange'], 'borderBottom':f"2px solid {C['ow_orange']}", 'textTransform':'uppercase'},
                page_size=10, sort_action="native",
                style_data_conditional=[{'if': {'column_id': 'win_rate', 'filter_query': '{win_rate} > 52'}, 'color': C['win'], 'fontWeight': 'bold'}]
            )
        ])
    ])
], className="ow-pattern")

# =============================================================
# CALLBACKS
# =============================================================
@app.callback(
    [Output('kpi-total','children'), Output('kpi-wr','children'), Output('kpi-pr','children'), Output('kpi-days','children'), Output('kpi-top','children'),
     Output('hero-of-the-day-section','children'), Output('hero-gallery-section','children'), Output('g-top10','figure'), Output('g-roles','figure'),
     Output('g-evol','figure'), Output('g-delta','figure'), Output('g-best-map','figure'), Output('g-radar','figure'),
     Output('g-box','figure'), Output('g-pvp','figure'), Output('g-mapa','figure'),
     Output('g-modo','figure'), Output('g-region','figure'), Output('g-scatter','figure'),
     Output('g-hist','figure'), Output('g-weekend','figure'),
     Output('g-bubble','figure'), Output('main-table','data'), Output('f-hero','options')],
    [Input('f-hero','value'), Input('f-rol','value'), Input('f-plat','value'), Input('f-date','start_date'), Input('f-date','end_date')]
)
def update_dashboard(heroes, roles, plats, sd, ed):
    d = df.copy()
    if heroes: d = d[d['nombre_heroe'].isin(heroes)]
    if roles:  d = d[d['rol'].isin(roles)]
    if plats:  d = d[d['plataforma'].isin(plats)]
    if sd: d = d[d['fecha'] >= pd.to_datetime(sd)]
    if ed: d = d[d['fecha'] <= pd.to_datetime(ed)]

    hero_opts = [{'label':h,'value':h} for h in sorted(df['nombre_heroe'].dropna().unique())]

    if d.empty:
        return ["0"] * 5 + [html.Div("SIN DATOS"), html.Div()] + [go.Figure()] * 15 + [[], hero_opts]

    # KPIs
    total_val = len(d)
    wr_avg = d['win_rate'].mean()
    pr_avg = d['pick_rate'].mean()
    days_count = d['fecha'].nunique()
    meta_hero = d.groupby('nombre_heroe')['win_rate'].mean().idxmax()

    # CÁLCULO DE ESTADÍSTICAS DEL ÚLTIMO DÍA (Para Héroe del Día, Top 10 y Galería)
    latest_date = d['fecha'].max()
    day_data = d[d['fecha'] == latest_date]
    if day_data.empty: day_data = d
    
    # Agrupamos una sola vez para asegurar consistencia absoluta
    day_stats_agg = day_data.groupby(['nombre_heroe','rol']).agg({'win_rate':'mean', 'pick_rate':'mean'}).reset_index()
    day_stats_agg = day_stats_agg.sort_values('win_rate', ascending=False)
    
    # Derivamos el Top 10 y el Héroe del Día
    top_day = day_stats_agg.nlargest(10, 'win_rate')
    top1 = top_day.iloc[0]
    
    hero_of_day_layout = html.Div([
        dbc.Row([
            dbc.Col(html.Div(style={**glass_card(C['ow_orange']), 'height':'100%', 'background':'linear-gradient(135deg, rgba(249, 158, 26, 0.4) 0%, rgba(0,0,0,0.85) 100%)', 'display':'flex', 'alignItems':'center'}, children=[
                html.Img(src=get_hero_img(top1['nombre_heroe']), className="hero-img-float", style={'height':'200px', 'marginRight':'30px'}),
                html.Div([
                    html.Small("HÉROE DEL DÍA", style={'letterSpacing':'4px', 'color':C['ow_orange'], 'fontWeight':'900'}),
                    html.H1(top1['nombre_heroe'].upper(), className="top1-glow", style={'fontSize':'80px', 'fontWeight':'900', 'margin':'0', 'color':'#fff', 'lineHeight':'1'}),
                    dbc.Row([
                        dbc.Col([
                            html.Div("VICTORIAS", style={'fontSize':'12px', 'color':C['sub']}),
                            html.H2(f"{top1['win_rate']:.1f}%", style={'color':C['win'], 'fontWeight':'900'})
                        ]),
                        dbc.Col([
                            html.Div("USO", style={'fontSize':'12px', 'color':C['sub']}),
                            html.H2(f"{top1['pick_rate']:.1f}%", style={'color':C['cyan'], 'fontWeight':'900'})
                        ]),
                        dbc.Col([
                            html.Div("ROL", style={'fontSize':'12px', 'color':C['sub']}),
                            html.H2(top1['rol'].upper(), style={'color':'#fff', 'fontSize':'24px', 'marginTop':'5px'})
                        ]),
                    ], style={'marginTop':'20px'})
                ])
            ]), width=7),
            
            dbc.Col(html.Div(style=glass_card(), children=[
                section_header("Top 10 de Hoy con Retratos", "⚔️"),
                html.Div([
                    html.Div(style={'display':'flex', 'justifyContent':'space-between', 'padding':'6px 0', 'borderBottom':'1px solid rgba(255,255,255,0.05)', 'alignItems':'center'}, children=[
                        html.Div([
                            html.Span(f"#{i+1} ", style={'color':C['ow_orange'], 'fontWeight':'bold', 'marginRight':'10px'}),
                            html.Img(src=get_hero_img(r['nombre_heroe']), style={'height':'35px', 'marginRight':'12px'}),
                            html.Span(r['nombre_heroe'], style={'fontWeight':'bold'})
                        ], style={'display':'flex', 'alignItems':'center'}),
                        html.Span(f"{r['win_rate']:.1f}% WR", style={'color':C['win'] if r['win_rate']>50 else C['lose']})
                    ]) for i, r in enumerate(top_day.iloc[1:].to_dict('records'))
                ])
            ]), width=5)
        ])
    ])

    # GALERÍA DE HÉROES (Sincronizada con el último registro disponible)
    hero_gallery_layout = html.Div(style=glass_card(), children=[
        section_header("Despliegue de Retratos de Combate (Official CDN - Última Jornada)", "🖼️"),
        dbc.Row([
            dbc.Col(html.Div(style={'textAlign':'center', 'padding':'10px', 'borderRadius':'8px', 'backgroundColor':'rgba(255,255,255,0.03)', 'border':'1px solid rgba(255,255,255,0.1)'}, className="hero-card-hover", children=[
                html.Img(src=get_hero_img(r['nombre_heroe']), style={'height':'60px', 'borderRadius':'50%', 'border':f'2px solid {C.get(r["rol"].lower(), C["sub"])}', 'marginBottom':'10px'}),
                html.Div(r['nombre_heroe'].upper(), style={'fontSize':'10px', 'fontWeight':'900', 'color':'#fff', 'whiteSpace':'nowrap', 'overflow':'hidden', 'textOverflow':'ellipsis'}),
            ]), width=1, style={'marginBottom':'15px', 'minWidth':'100px'}) for r in day_stats_agg.to_dict('records')
        ], justify="start", style={'display':'flex', 'flexWrap':'wrap'})
    ])

    # 1. Top 10
    f1 = px.bar(top_day, x='win_rate', y='nombre_heroe', color='rol', orientation='h', 
                color_discrete_map={'tank':C['tank'],'damage':C['damage'],'support':C['support']},
                text_auto='.1f')
    f1.update_layout(PLOT_LAYOUT, xaxis_title="Victoria %", yaxis_title="", showlegend=False)

    # 2. Roles
    f2 = px.pie(d.groupby('rol').size().reset_index(name='c'), values='c', names='rol', hole=0.6,
                color='rol', color_discrete_map={'tank':C['tank'],'damage':C['damage'],'support':C['support']})
    f2.update_layout(PLOT_LAYOUT)

    # 3. Evolución
    top_evol = d.groupby('nombre_heroe')['win_rate'].mean().nlargest(8).index
    d_evol = d[d['nombre_heroe'].isin(top_evol)].groupby(['fecha','nombre_heroe'])['win_rate'].mean().reset_index()
    f3 = px.line(d_evol, x='fecha', y='win_rate', color='nombre_heroe', color_discrete_sequence=px.colors.qualitative.Alphabet)
    f3.update_traces(line=dict(width=3))
    f3.update_layout(PLOT_LAYOUT, xaxis_title="Fecha", yaxis_title="Win Rate %")

    # 4. Impulso
    fs = sorted(d['fecha'].unique())
    if len(fs)>1:
        m = fs[len(fs)//2]
        v1 = d[d['fecha']<=m].groupby('nombre_heroe')['win_rate'].mean()
        v2 = d[d['fecha']>m].groupby('nombre_heroe')['win_rate'].mean()
        diff = (v2-v1).dropna().reset_index()
        diff_top = pd.concat([diff.nlargest(5, 'win_rate'), diff.nsmallest(5, 'win_rate')])
        f4 = px.bar(diff_top, x='nombre_heroe', y='win_rate', color='win_rate', color_continuous_scale='RdYlGn')
        f4.update_layout(PLOT_LAYOUT, showlegend=False, coloraxis_showscale=False)
    else: f4 = go.Figure()

    # 5. MEJOR HÉROE POR MAPA
    if 'mapa' in d.columns:
        agg_map_hero = d.groupby(['mapa', 'nombre_heroe', 'rol'])['win_rate'].mean().reset_index()
        best_per_map = agg_map_hero.sort_values('win_rate', ascending=False).drop_duplicates('mapa').sort_values('mapa')
        f_best_map = px.bar(best_per_map, x='win_rate', y='mapa', color='rol', text='nombre_heroe',
                           color_discrete_map={'tank':C['tank'],'damage':C['damage'],'support':C['support']},
                           labels={'win_rate':'Win Rate %', 'mapa':'Mapa', 'nombre_heroe':'Héroe'})
        f_best_map.update_layout(PLOT_LAYOUT, barmode='group')
    else: f_best_map = go.Figure()

    # 6. Radar
    agg_radar = d.groupby('rol')[['win_rate','pick_rate']].mean().reset_index()
    f5 = go.Figure()
    for r in agg_radar['rol'].unique():
        row = agg_radar[agg_radar['rol']==r]
        f5.add_trace(go.Scatterpolar(r=[row['win_rate'].iloc[0], row['pick_rate'].iloc[0]*5, row['win_rate'].iloc[0]], 
                                     theta=['Victoria','Uso','Victoria'], fill='toself', name=r))
    f5.update_layout(PLOT_LAYOUT, polar=dict(bgcolor='rgba(0,0,0,0)', radialaxis=dict(visible=True, range=[0, 75])))

    # 7. Box Plot
    f6 = px.box(d, x='rol', y='win_rate', color='rol', color_discrete_map={'tank':C['tank'],'damage':C['damage'],'support':C['support']})
    f6.update_layout(PLOT_LAYOUT)

    # 8. Plataforma
    f7 = px.bar(d.groupby('plataforma')['win_rate'].mean().reset_index(), x='plataforma', y='win_rate', color='plataforma', text_auto='.1f')
    f7.update_layout(PLOT_LAYOUT, showlegend=False)

    # 9. Mapa
    if 'mapa' in d.columns:
        agg_map = d.groupby('mapa')['win_rate'].mean().reset_index().nlargest(15, 'win_rate')
        f8 = px.bar(agg_map, x='win_rate', y='mapa', color='win_rate', color_continuous_scale='YlOrRd')
        f8.update_layout(PLOT_LAYOUT, coloraxis_showscale=False)
    else: f8 = go.Figure()

    # 10. Modo Treemap
    if 'modo_juego' in d.columns:
        f9 = px.treemap(d.groupby(['modo_juego','rol']).size().reset_index(name='count'), path=['modo_juego','rol'], values='count', color='rol',
                        color_discrete_map={'tank':C['tank'],'damage':C['damage'],'support':C['support']})
        f9.update_layout(PLOT_LAYOUT)
    else: f9 = go.Figure()

    # 11. Region
    if 'region' in d.columns:
        f10 = px.funnel(d.groupby('region')['win_rate'].mean().reset_index().sort_values('win_rate', ascending=False), y='region', x='win_rate')
        f10.update_layout(PLOT_LAYOUT)
    else: f10 = go.Figure()

    # 12. Scatter
    agg_s = d.groupby(['nombre_heroe','rol']).agg({'win_rate':'mean','pick_rate':'mean'}).reset_index()
    f11 = px.scatter(agg_s, x='pick_rate', y='win_rate', color='rol', size='pick_rate', hover_name='nombre_heroe', text='nombre_heroe',
                     color_discrete_map={'tank':C['tank'],'damage':C['damage'],'support':C['support']})
    f11.update_layout(PLOT_LAYOUT)

    # 13. Histogram
    f12 = px.histogram(d, x='win_rate', nbins=30, color_discrete_sequence=[C['ow_orange']])
    f12.update_layout(PLOT_LAYOUT)

    # 14. Factor Finde
    f14 = px.bar(d.groupby('es_finde')['win_rate'].mean().reset_index(), x='es_finde', y='win_rate', color='es_finde', text_auto='.1f')
    f14.update_layout(PLOT_LAYOUT, showlegend=False)

    # 15. Bubble
    f15 = px.scatter(agg_s, x='nombre_heroe', y='win_rate', size='pick_rate', color='win_rate', color_continuous_scale='Portland')
    f15.update_layout(PLOT_LAYOUT, coloraxis_showscale=False)

    # Table
    t_df = d.groupby(['nombre_heroe','rol'])[['win_rate','pick_rate']].mean().reset_index().nlargest(50, 'win_rate')
    t_df['win_rate'] = t_df['win_rate'].round(1)
    t_df['pick_rate'] = t_df['pick_rate'].round(1)
    t = t_df.to_dict('records')

    return f"{total_val:,}", f"{wr_avg:.1f}%", f"{pr_avg:.1f}%", f"{days_count}", meta_hero, hero_of_day_layout, hero_gallery_layout, f1, f2, f3, f4, f_best_map, f5, f6, f7, f8, f9, f10, f11, f12, f14, f15, t, hero_opts


if __name__ == '__main__':
    # Usamos el puerto que nos dé el servidor o el 8052 por defecto
    port = int(os.environ.get("PORT", 8052))
    app.run(debug=False, host='0.0.0.0', port=port)
