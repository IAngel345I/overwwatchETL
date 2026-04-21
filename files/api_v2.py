
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pg8000.dbapi
import logging

from etl_v2 import run_etl, connect_db

log = logging.getLogger("api_v2")

# ─────────────────────────────────────────────
# SCHEDULER - corre el ETL cada semana a las 2:00 PM
# ─────────────────────────────────────────────
scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(
        run_etl,
        trigger=CronTrigger(day_of_week="mon", hour=14, minute=0),  # Lunes a las 2:00 PM
        id="etl_semanal",
        replace_existing=True,
        misfire_grace_time=28800,  # Corre si abres uvicorn entre 2:00 PM y 10:00 PM del lunes
    )
    scheduler.start()
    log.info("Scheduler iniciado - ETL programado todos los lunes a las 2:00 PM")
    yield
    scheduler.shutdown()
    log.info("Scheduler detenido")

app = FastAPI(
    title="Overwatch 2 BI - API v2",
    description="ETL automatico semanal los lunes a las 2:00 PM con registro en dim_tiempo",
    version="2.2.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def query_db(sql: str, params=None) -> list[dict]:
    conn = connect_db()
    try:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        conn.close()


# ─────────────────────────────────────────────
# ETL
# ─────────────────────────────────────────────
@app.post("/etl/run", tags=["ETL"])
def run_full_etl(background: BackgroundTasks):
    """Corre el ETL manualmente en background."""
    background.add_task(run_etl)
    return {"status": "ETL iniciado en background"}

@app.get("/etl/proxima-ejecucion", tags=["ETL"])
def proxima_ejecucion():
    """Muestra cuando sera la proxima ejecucion automatica (lunes 2:00 PM)."""
    job = scheduler.get_job("etl_semanal")
    if job:
        return {"proxima_ejecucion": str(job.next_run_time)}
    return {"proxima_ejecucion": "No programada"}


# ─────────────────────────────────────────────
# DIMENSIONES
# ─────────────────────────────────────────────
@app.get("/heroes", tags=["Dimensiones"])
def get_heroes(rol: str = None):
    """Lista todos los heroes. Filtra por rol: tank, damage, support."""
    sql = "SELECT * FROM public.dim_heroe"
    params = []
    if rol:
        sql += " WHERE LOWER(rol) = LOWER(%s)"
        params.append(rol)
    return query_db(sql, params)

@app.get("/snapshots", tags=["Dimensiones"])
def get_snapshots():
    """Lista todos los snapshots registrados en dim_tiempo."""
    sql = """
        SELECT id_tiempo, fecha, hora, dia_semana, mes, anio
        FROM public.dim_tiempo
        ORDER BY fecha DESC, hora DESC
    """
    return query_db(sql)

@app.get("/mapas", tags=["Dimensiones"])
def get_mapas(region: str = None):
    """Lista todos los mapas disponibles."""
    sql = "SELECT * FROM public.dim_escenario"
    params = []
    if region:
        sql += " WHERE LOWER(region) = LOWER(%s)"
        params.append(region)
    sql += " ORDER BY region, mapa"
    return query_db(sql, params)


# ─────────────────────────────────────────────
# ANALISIS - ULTIMO SNAPSHOT
# ─────────────────────────────────────────────
@app.get("/rates/latest", tags=["Analisis"])
def get_latest_rates(plataforma: str = None, region: str = None, mapa: str = None):
    """Rates del ultimo snapshot registrado."""
    sql = """
        SELECT
            h.nombre_heroe, h.rol,
            c.plataforma, c.modo_juego,
            e.region, e.mapa,
            f.win_rate, f.pick_rate,
            t.fecha, t.hora
        FROM public.fact_hero_rates f
        JOIN public.dim_heroe     h ON h.id_heroe     = f.id_heroe
        JOIN public.dim_contexto  c ON c.id_contexto  = f.id_contexto
        JOIN public.dim_escenario e ON e.id_escenario = f.id_escenario
        JOIN public.dim_tiempo    t ON t.id_tiempo     = f.id_tiempo
        WHERE f.id_tiempo = (SELECT MAX(id_tiempo) FROM public.fact_hero_rates)
    """
    params = []
    if plataforma:
        sql += " AND LOWER(c.plataforma) = LOWER(%s)"
        params.append(plataforma)
    if region:
        sql += " AND LOWER(e.region) = LOWER(%s)"
        params.append(region)
    if mapa:
        sql += " AND LOWER(e.mapa) = LOWER(%s)"
        params.append(mapa)
    sql += " ORDER BY f.win_rate DESC NULLS LAST"
    return query_db(sql, params)


@app.get("/rates/top-winrate", tags=["Analisis"])
def top_winrate(limit: int = 10, plataforma: str = "PC", region: str = "Americas", mapa: str = "Busan"):
    """Top heroes por win rate en el ultimo snapshot."""
    sql = """
        SELECT h.nombre_heroe, h.rol, f.win_rate, f.pick_rate, t.fecha, t.hora
        FROM public.fact_hero_rates f
        JOIN public.dim_heroe     h ON h.id_heroe     = f.id_heroe
        JOIN public.dim_contexto  c ON c.id_contexto  = f.id_contexto
        JOIN public.dim_escenario e ON e.id_escenario = f.id_escenario
        JOIN public.dim_tiempo    t ON t.id_tiempo     = f.id_tiempo
        WHERE f.id_tiempo = (SELECT MAX(id_tiempo) FROM public.fact_hero_rates)
          AND LOWER(c.plataforma) = LOWER(%s)
          AND LOWER(e.region)     = LOWER(%s)
          AND LOWER(e.mapa)       = LOWER(%s)
        ORDER BY f.win_rate DESC NULLS LAST
        LIMIT %s
    """
    return query_db(sql, (plataforma, region, mapa, limit))


@app.get("/rates/top-pickrate", tags=["Analisis"])
def top_pickrate(limit: int = 10, plataforma: str = "PC", region: str = "Americas", mapa: str = "Busan"):
    """Top heroes por pick rate en el ultimo snapshot."""
    sql = """
        SELECT h.nombre_heroe, h.rol, f.win_rate, f.pick_rate, t.fecha, t.hora
        FROM public.fact_hero_rates f
        JOIN public.dim_heroe     h ON h.id_heroe     = f.id_heroe
        JOIN public.dim_contexto  c ON c.id_contexto  = f.id_contexto
        JOIN public.dim_escenario e ON e.id_escenario = f.id_escenario
        JOIN public.dim_tiempo    t ON t.id_tiempo     = f.id_tiempo
        WHERE f.id_tiempo = (SELECT MAX(id_tiempo) FROM public.fact_hero_rates)
          AND LOWER(c.plataforma) = LOWER(%s)
          AND LOWER(e.region)     = LOWER(%s)
          AND LOWER(e.mapa)       = LOWER(%s)
        ORDER BY f.pick_rate DESC NULLS LAST
        LIMIT %s
    """
    return query_db(sql, (plataforma, region, mapa, limit))


@app.get("/rates/por-mapa", tags=["Analisis"])
def rates_por_mapa(heroe: str, plataforma: str = "PC", region: str = "Americas"):
    """Win rate de un heroe en cada mapa en el ultimo snapshot."""
    sql = """
        SELECT e.mapa, f.win_rate, f.pick_rate, c.modo_juego
        FROM public.fact_hero_rates f
        JOIN public.dim_heroe     h ON h.id_heroe     = f.id_heroe
        JOIN public.dim_contexto  c ON c.id_contexto  = f.id_contexto
        JOIN public.dim_escenario e ON e.id_escenario = f.id_escenario
        WHERE LOWER(h.nombre_heroe) = LOWER(%s)
          AND LOWER(c.plataforma)   = LOWER(%s)
          AND LOWER(e.region)       = LOWER(%s)
          AND f.id_tiempo = (SELECT MAX(id_tiempo) FROM public.fact_hero_rates)
        ORDER BY f.win_rate DESC
    """
    return query_db(sql, (heroe, plataforma, region))


@app.get("/rates/comparar-regiones", tags=["Analisis"])
def comparar_regiones(heroe: str, plataforma: str = "PC", mapa: str = "Busan"):
    """Compara win rate de un heroe entre Americas, Asia y Europa."""
    sql = """
        SELECT e.region, f.win_rate, f.pick_rate, t.fecha, t.hora
        FROM public.fact_hero_rates f
        JOIN public.dim_heroe     h ON h.id_heroe     = f.id_heroe
        JOIN public.dim_contexto  c ON c.id_contexto  = f.id_contexto
        JOIN public.dim_escenario e ON e.id_escenario = f.id_escenario
        JOIN public.dim_tiempo    t ON t.id_tiempo     = f.id_tiempo
        WHERE LOWER(h.nombre_heroe) = LOWER(%s)
          AND LOWER(c.plataforma)   = LOWER(%s)
          AND LOWER(e.mapa)         = LOWER(%s)
          AND f.id_tiempo = (SELECT MAX(id_tiempo) FROM public.fact_hero_rates)
        ORDER BY e.region
    """
    return query_db(sql, (heroe, plataforma, mapa))


# ─────────────────────────────────────────────
# HISTORICO
# ─────────────────────────────────────────────
@app.get("/rates/heroe/{nombre}", tags=["Historico"])
def heroe_historico(nombre: str):
    """Historial completo de un heroe en todos los snapshots."""
    sql = """
        SELECT
            t.fecha, t.hora, t.dia_semana,
            c.plataforma, c.modo_juego,
            e.region, e.mapa,
            f.win_rate, f.pick_rate
        FROM public.fact_hero_rates f
        JOIN public.dim_heroe     h ON h.id_heroe     = f.id_heroe
        JOIN public.dim_contexto  c ON c.id_contexto  = f.id_contexto
        JOIN public.dim_escenario e ON e.id_escenario = f.id_escenario
        JOIN public.dim_tiempo    t ON t.id_tiempo     = f.id_tiempo
        WHERE LOWER(h.nombre_heroe) = LOWER(%s)
        ORDER BY t.fecha DESC, t.hora DESC
    """
    rows = query_db(sql, (nombre,))
    if not rows:
        raise HTTPException(404, f"Heroe '{nombre}' no encontrado")
    return rows


@app.get("/rates/evolucion", tags=["Historico"])
def evolucion_heroe(heroe: str, plataforma: str = "PC", region: str = "Americas", mapa: str = "Busan"):
    """Evolucion de win rate y pick rate de un heroe dia a dia."""
    sql = """
        SELECT t.fecha, t.hora, t.dia_semana, f.win_rate, f.pick_rate
        FROM public.fact_hero_rates f
        JOIN public.dim_heroe     h ON h.id_heroe     = f.id_heroe
        JOIN public.dim_contexto  c ON c.id_contexto  = f.id_contexto
        JOIN public.dim_escenario e ON e.id_escenario = f.id_escenario
        JOIN public.dim_tiempo    t ON t.id_tiempo     = f.id_tiempo
        WHERE LOWER(h.nombre_heroe) = LOWER(%s)
          AND LOWER(c.plataforma)   = LOWER(%s)
          AND LOWER(e.region)       = LOWER(%s)
          AND LOWER(e.mapa)         = LOWER(%s)
        ORDER BY t.fecha ASC, t.hora ASC
    """
    rows = query_db(sql, (heroe, plataforma, region, mapa))
    if not rows:
        raise HTTPException(404, f"Sin datos para '{heroe}' en {mapa}")
    return rows


@app.get("/rates/comparar-fechas", tags=["Historico"])
def comparar_fechas(heroe: str, fecha1: str, fecha2: str, plataforma: str = "PC", region: str = "Americas", mapa: str = "Busan"):
    """Compara el rendimiento de un heroe entre dos fechas (formato YYYY-MM-DD)."""
    sql = """
        SELECT t.fecha, t.hora, f.win_rate, f.pick_rate
        FROM public.fact_hero_rates f
        JOIN public.dim_heroe     h ON h.id_heroe     = f.id_heroe
        JOIN public.dim_contexto  c ON c.id_contexto  = f.id_contexto
        JOIN public.dim_escenario e ON e.id_escenario = f.id_escenario
        JOIN public.dim_tiempo    t ON t.id_tiempo     = f.id_tiempo
        WHERE LOWER(h.nombre_heroe) = LOWER(%s)
          AND LOWER(c.plataforma)   = LOWER(%s)
          AND LOWER(e.region)       = LOWER(%s)
          AND LOWER(e.mapa)         = LOWER(%s)
          AND t.fecha IN (%s, %s)
        ORDER BY t.fecha ASC
    """
    return query_db(sql, (heroe, plataforma, region, mapa, fecha1, fecha2))


@app.get("/", tags=["Health"])
def root():
    return {"message": "Overwatch 2 BI API v2.2 - ETL automatico todos los lunes a las 2:00 PM"}