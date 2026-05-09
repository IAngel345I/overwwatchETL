import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
import os

# Configuración de la página
st.set_page_config(page_title="Overwatch BI", layout="wide", page_icon="🎮")

# Estilos Premium (CSS)
st.markdown("""
    <style>
    .main { background-color: #08080a; color: white; }
    .stMetric { background-color: rgba(25, 25, 35, 0.85); border: 1px solid #f99e1a; padding: 15px; border-radius: 10px; }
    h1, h2, h3 { color: #f99e1a !important; font-family: 'Inter', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# Conexion a DB
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://neondb_owner:npg_nO2jVToBf8RH@ep-broad-union-aqbrnfsq.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require")
engine = create_engine(DATABASE_URL)

@st.cache_data(ttl=600)
def load_data():
    SQL_RATES = """
        SELECT h.nombre_heroe, h.rol, c.plataforma, c.modo_juego, 
               e.region, e.mapa, f.win_rate, f.pick_rate,
               t.fecha, t.dia_semana, t.mes, t.anio
        FROM public.fact_hero_rates f
        JOIN public.dim_heroes h ON f.id_heroe = h.id_heroe
        JOIN public.dim_contexto c ON f.id_contexto = c.id_contexto
        JOIN public.dim_escenario e ON f.id_escenario = e.id_escenario
        JOIN public.dim_tiempo t ON f.id_tiempo = t.id_tiempo
    """
    SQL_STATS = """
        SELECT h.nombre_heroe, h.rol, c.plataforma, c.modo_juego,
               e.region, e.mapa, f.eliminations_avg, f.deaths_avg, f.damage_avg, f.healing_avg,
               t.fecha, t.dia_semana, t.mes, t.anio
        FROM public.fact_hero_stats f
        JOIN public.dim_heroes h ON f.id_heroe = h.id_heroe
        JOIN public.dim_contexto c ON f.id_contexto = c.id_contexto
        JOIN public.dim_escenario e ON f.id_escenario = e.id_escenario
        JOIN public.dim_tiempo t ON f.id_tiempo = t.id_tiempo
    """
    try:
        with engine.connect() as conn:
            df1 = pd.read_sql(SQL_RATES, conn)
            df2 = pd.read_sql(SQL_STATS, conn)
        return pd.concat([df1, df2], ignore_index=True, sort=False)
    except Exception as e:
        print(f"Error: {e}")
        return pd.DataFrame()

# Título
st.title("🛡️ OVERWATCH BI | Inteligencia Estratégica")

# Cargar Datos
df = load_data()

if df.empty:
    st.error("No se pudieron cargar los datos. Verifica DATABASE_URL.")
else:
    # Sidebar Filtros
    st.sidebar.header("Filtros de Inteligencia")
    heroes = st.sidebar.multiselect("Héroes", sorted(df['nombre_heroe'].unique()))
    roles = st.sidebar.multiselect("Roles", df['rol'].unique())
    
    # Filtrado
    d = df.copy()
    if heroes: d = d[d['nombre_heroe'].isin(heroes)]
    if roles: d = d[d['rol'].isin(roles)]

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Muestras", len(d))
    c2.metric("Win Rate Promedio", f"{d['win_rate'].mean():.1f}%")
    c3.metric("Pick Rate Promedio", f"{d['pick_rate'].mean():.1f}%")
    c4.metric("Días Registrados", d['fecha'].nunique())

    # Gráficos Principales
    st.subheader("Análisis de Rendimiento")
    col_a, col_b = st.columns(2)
    
    with col_a:
        fig1 = px.bar(d.groupby('nombre_heroe')['win_rate'].mean().reset_index().nlargest(10, 'win_rate'), 
                      x='win_rate', y='nombre_heroe', title="Top 10 Win Rate", color='win_rate')
        st.plotly_chart(fig1, use_container_width=True)
        
    with col_b:
        fig2 = px.pie(d, names='rol', title="Distribución de Roles")
        st.plotly_chart(fig2, use_container_width=True)

    # Tabla
    st.subheader("Registro Detallado")
    st.dataframe(d.head(100), use_container_width=True)
