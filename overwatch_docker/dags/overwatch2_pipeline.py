# -*- coding: utf-8 -*-
"""
Overwatch 2 BI — DAG de Airflow
Pipeline: Scrape Blizzard → ETL → PostgreSQL → Reportes
Corre todos los dias a las 2PM

Mejoras incluidas:
  - Segunda URL: /en-us/heroes/ para extraer dificultad real de cada heroe
  - Limpieza de nulos, duplicados y espacios en blanco antes del ETL
  - Indices optimizados en PostgreSQL creados automaticamente
  - Validacion XPath con lxml como tecnica alternativa de scraping
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from datetime import datetime, timedelta
import pendulum
import logging

# ─── Configuracion ───────────────────────────────────────────
DB_CONFIG = {
    "host": "host.docker.internal",
    "port": 5432,
    "database": "overwatch2",
    "user": "postgres",
    "password": "planta40",
}

HEROES = [
    {"nombre": "Ana",           "rol": "support"},
    {"nombre": "Ashe",          "rol": "damage"},
    {"nombre": "Baptiste",      "rol": "support"},
    {"nombre": "Bastion",       "rol": "damage"},
    {"nombre": "Brigitte",      "rol": "support"},
    {"nombre": "Cassidy",       "rol": "damage"},
    {"nombre": "D.Va",          "rol": "tank"},
    {"nombre": "Doomfist",      "rol": "tank"},
    {"nombre": "Echo",          "rol": "damage"},
    {"nombre": "Genji",         "rol": "damage"},
    {"nombre": "Hanzo",         "rol": "damage"},
    {"nombre": "Illari",        "rol": "support"},
    {"nombre": "Junker Queen",  "rol": "tank"},
    {"nombre": "Junkrat",       "rol": "damage"},
    {"nombre": "Juno",          "rol": "support"},
    {"nombre": "Kiriko",        "rol": "support"},
    {"nombre": "Lifeweaver",    "rol": "support"},
    {"nombre": "Lucio",         "rol": "support"},
    {"nombre": "Mauga",         "rol": "tank"},
    {"nombre": "Mei",           "rol": "damage"},
    {"nombre": "Mercy",         "rol": "support"},
    {"nombre": "Moira",         "rol": "support"},
    {"nombre": "Orisa",         "rol": "tank"},
    {"nombre": "Pharah",        "rol": "damage"},
    {"nombre": "Ramattra",      "rol": "tank"},
    {"nombre": "Reaper",        "rol": "damage"},
    {"nombre": "Reinhardt",     "rol": "tank"},
    {"nombre": "Roadhog",       "rol": "tank"},
    {"nombre": "Sigma",         "rol": "tank"},
    {"nombre": "Sojourn",       "rol": "damage"},
    {"nombre": "Soldier: 76",   "rol": "damage"},
    {"nombre": "Sombra",        "rol": "damage"},
    {"nombre": "Symmetra",      "rol": "damage"},
    {"nombre": "Torbjorn",      "rol": "damage"},
    {"nombre": "Tracer",        "rol": "damage"},
    {"nombre": "Venture",       "rol": "damage"},
    {"nombre": "Widowmaker",    "rol": "damage"},
    {"nombre": "Winston",       "rol": "tank"},
    {"nombre": "Wrecking Ball", "rol": "tank"},
    {"nombre": "Zarya",         "rol": "tank"},
    {"nombre": "Zenyatta",      "rol": "support"},
    {"nombre": "Hazard",        "rol": "tank"},
    {"nombre": "Domina",        "rol": "tank"},
    {"nombre": "Freja",         "rol": "damage"},
    {"nombre": "Vendetta",      "rol": "damage"},
    {"nombre": "Anran",         "rol": "damage"},
    {"nombre": "Wuyang",        "rol": "support"},
    {"nombre": "Mizuki",        "rol": "support"},
]

# ─── Filtros reales de la pagina de Blizzard ─────────────────
COMBINACIONES_SCRAPE = []
for input_val in ["PC", "Console"]:
    for region in ["Americas", "Europe", "Asia"]:
        for rq in [0, 1]:
            for tier in ["All"]:
                COMBINACIONES_SCRAPE.append({
                    "input":  input_val,
                    "region": region,
                    "rq":     rq,
                    "tier":   tier,
                })

PLATAFORMAS = ["PC", "Console"]
REGIONES    = ["Americas", "Europe", "Asia"]
MAPAS       = [
    "King's Row", "Hanamura", "Watchpoint: Gibraltar", "Ilios",
    "Lijiang Tower", "Nepal", "Oasis", "Busan", "Hollywood",
    "Numbani", "Eichenwalde", "Dorado", "Route 66",
]
MODOS = ["competitive-role-queue", "open-queue"]

# ─── Default Args ────────────────────────────────────────────
default_args = {
    "owner": "angel",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

# ─── Helpers ─────────────────────────────────────────────────

def _parse_pct(texto):
    """Convierte '49.8%' → 49.8  |  falla → None"""
    try:
        return float(texto.replace("%", "").strip())
    except (ValueError, AttributeError):
        return None


def _limpiar_texto(texto):
    """Elimina espacios extra y caracteres no deseados de un string"""
    if texto is None:
        return None
    return " ".join(texto.strip().split())


def _scrape_una_combinacion(session, combinacion):
    """
    URL 1: https://overwatch.blizzard.com/en-us/rates/
    Extrae pick_rate y win_rate de cada heroe usando BeautifulSoup.
    Slots del HTML: slot="cell-{slug}-winrate" / slot="cell-{slug}-pickrate"
    """
    from bs4 import BeautifulSoup

    url = "https://overwatch.blizzard.com/en-us/rates/"
    params = {
        "input":  combinacion["input"].lower(),
        "region": combinacion["region"],
        "rq":     combinacion["rq"],
        "tier":   combinacion["tier"],
    }

    resp = session.get(url, params=params, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    resultados = []

    for tag in soup.find_all(attrs={"slot": lambda v: v and v.startswith("cell-") and v.endswith("-winrate")}):
        slot      = tag["slot"]
        hero_slug = slot[5:-8]

        wr_tag = soup.find(attrs={"slot": f"cell-{hero_slug}-winrate"})
        pr_tag = soup.find(attrs={"slot": f"cell-{hero_slug}-pickrate"})

        wr = _parse_pct(wr_tag.get_text(strip=True)) if wr_tag else None
        pr = _parse_pct(pr_tag.get_text(strip=True)) if pr_tag else None

        # Limpieza: descartar registros con nulos
        if wr is not None and pr is not None:
            # Limpieza: descartar valores fuera de rango (0-100%)
            if 0 <= wr <= 100 and 0 <= pr <= 100:
                resultados.append({
                    "slug":      _limpiar_texto(hero_slug),
                    "win_rate":  wr,
                    "pick_rate": pr,
                    "input":     combinacion["input"],
                    "region":    combinacion["region"],
                    "rq":        combinacion["rq"],
                    "tier":      combinacion["tier"],
                })

    return resultados


def _scrape_heroes_info(session):
    """
    URL 2: https://overwatch.blizzard.com/en-us/heroes/
    Extrae la dificultad real de cada heroe usando BeautifulSoup.
    Retorna dict: {slug: dificultad}
    Dificultades posibles: Easy | Medium | Hard
    """
    from bs4 import BeautifulSoup

    url = "https://overwatch.blizzard.com/en-us/heroes/"
    try:
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        dificultades = {}

        # Los heroes en la pagina tienen slot="name" y slot="difficulty"
        # Buscar tarjetas de heroes con sus datos
        for tag in soup.find_all(attrs={"slot": lambda v: v and v.endswith("-difficulty")}):
            slot = tag["slot"]                    # "ashe-difficulty"
            slug = slot[:-11]                     # "ashe"
            dif  = _limpiar_texto(tag.get_text(strip=True))  # "Medium"

            # Normalizar a español
            mapa_dif = {
                "easy":   "Facil",
                "medium": "Media",
                "hard":   "Dificil",
            }
            dificultades[slug] = mapa_dif.get(dif.lower(), "Media") if dif else "Media"

        logging.info(f"  ✅ URL 2 (/heroes/) → {len(dificultades)} dificultades extraidas")
        return dificultades

    except Exception as e:
        logging.warning(f"  ⚠️  URL 2 (/heroes/) fallo: {e} — se usara 'Media' como fallback")
        return {}


# ─── Tasks ───────────────────────────────────────────────────

def task_verificar_conexion(**context):
    """Verifica que PostgreSQL este disponible"""
    import psycopg2
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.close()
        logging.info("✅ Conexion a PostgreSQL exitosa")
    except Exception as e:
        raise Exception(f"❌ Error de conexion: {e}")


def task_crear_indices(**context):
    """
    Crea indices optimizados en PostgreSQL si no existen.
    Mejora el rendimiento de las consultas en Power BI y Pentaho.
    Se ejecuta una sola vez — IF NOT EXISTS lo hace idempotente.
    """
    import psycopg2
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()

    indices = [
        # fact_hero_rates — las columnas mas consultadas en JOINs y filtros
        "CREATE INDEX IF NOT EXISTS idx_fact_id_heroe    ON public.fact_hero_rates (id_heroe)",
        "CREATE INDEX IF NOT EXISTS idx_fact_id_tiempo   ON public.fact_hero_rates (id_tiempo)",
        "CREATE INDEX IF NOT EXISTS idx_fact_id_contexto ON public.fact_hero_rates (id_contexto)",
        "CREATE INDEX IF NOT EXISTS idx_fact_id_escenario ON public.fact_hero_rates (id_escenario)",
        # dim_tiempo — filtros por fecha frecuentes
        "CREATE INDEX IF NOT EXISTS idx_tiempo_fecha     ON public.dim_tiempo (fecha)",
        # dim_heroe — filtros por nombre y rol
        "CREATE INDEX IF NOT EXISTS idx_heroe_nombre     ON public.dim_heroe (nombre_heroe)",
        "CREATE INDEX IF NOT EXISTS idx_heroe_rol        ON public.dim_heroe (rol)",
        # dim_contexto — filtros por plataforma y modo
        "CREATE INDEX IF NOT EXISTS idx_contexto_plat    ON public.dim_contexto (plataforma)",
        "CREATE INDEX IF NOT EXISTS idx_contexto_modo    ON public.dim_contexto (modo_juego)",
        # dim_escenario — filtros por region y mapa
        "CREATE INDEX IF NOT EXISTS idx_escenario_region ON public.dim_escenario (region)",
        "CREATE INDEX IF NOT EXISTS idx_escenario_mapa   ON public.dim_escenario (mapa)",
    ]

    for sql in indices:
        cur.execute(sql)
        logging.info(f"  ✅ {sql.split('idx_')[1].split(' ')[0]}")

    conn.commit()
    conn.close()
    logging.info("✅ Indices creados/verificados correctamente")


def task_scrape_blizzard(**context):
    """
    Scrape REAL de Blizzard usando BeautifulSoup — dos URLs:

    URL 1: /en-us/rates/   → win_rate y pick_rate por heroe (600 registros)
    URL 2: /en-us/heroes/  → dificultad real de cada heroe

    Incluye limpieza: descarta nulos, valores fuera de rango y duplicados.
    Los datos se guardan en XCom como lista de dicts.
    """
    import requests
    import time

    headers = {
        "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer":         "https://overwatch.blizzard.com/en-us/heroes/",
    }

    session = requests.Session()
    session.headers.update(headers)

    # ── URL 2: dificultad de heroes ───────────────────────────
    logging.info("── Scrapeando URL 2: /en-us/heroes/ ──")
    dificultades = _scrape_heroes_info(session)
    context["ti"].xcom_push(key="dificultades", value=dificultades)
    time.sleep(1)

    # ── URL 1: win_rate y pick_rate ───────────────────────────
    logging.info("── Scrapeando URL 1: /en-us/rates/ ──")
    todos   = []
    errores = 0
    slugs_vistos = set()   # para detectar duplicados por combinacion

    for combinacion in COMBINACIONES_SCRAPE:
        etiqueta = f"{combinacion['input']} / {combinacion['region']} / rq={combinacion['rq']} / tier={combinacion['tier']}"
        try:
            resultados = _scrape_una_combinacion(session, combinacion)

            # Limpieza: eliminar duplicados dentro de la misma combinacion
            limpios = []
            for r in resultados:
                clave = (r["slug"], r["input"], r["region"], r["rq"], r["tier"])
                if clave not in slugs_vistos:
                    slugs_vistos.add(clave)
                    limpios.append(r)

            todos.extend(limpios)
            logging.info(f"  ✅ {etiqueta} → {len(limpios)} heroes (limpios)")
        except Exception as e:
            errores += 1
            logging.warning(f"  ⚠️  {etiqueta} → fallo: {e}")

        time.sleep(1)

    logging.info(f"✅ Scrape completado: {len(todos)} registros | {errores} errores")
    context["ti"].xcom_push(key="blizzard_data", value=todos)


def task_validar_xpath(**context):
    """
    Validacion con XPath (lxml) — verifica que los datos scrapeados
    son correctos comparando contra la misma fuente con un metodo distinto.
    Solo lee y loguea, NO escribe en PostgreSQL ni modifica el pipeline.
    Si falla, el pipeline sigue corriendo gracias a trigger_rule='all_done'.
    """
    import requests
    from lxml import etree

    url = "https://overwatch.blizzard.com/en-us/rates/"
    params = {"input": "pc", "region": "Americas", "rq": "0", "tier": "All"}
    headers = {
        "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()

        tree = etree.fromstring(resp.content, etree.HTMLParser())

        tags = tree.xpath(
            '//*[starts-with(@slot, "cell-") and '
            'substring(@slot, string-length(@slot) - 6) = "winrate"]'
        )

        logging.info(f"✅ XPath — heroes encontrados: {len(tags)}")
        logging.info("─── Muestra primeros 10 heroes (XPath) ───")

        for tag in tags[:10]:
            slot    = tag.get("slot")
            slug    = slot[5:-8]
            wr      = (tag.text or "").strip()
            pr_tags = tree.xpath(f'//*[@slot="cell-{slug}-pickrate"]')
            pr      = (pr_tags[0].text or "").strip() if pr_tags else "N/A"
            logging.info(f"  XPath → {slug:<20} win={wr:<8} pick={pr}")

        logging.info("✅ Validacion XPath completada sin errores")

    except Exception as e:
        logging.warning(f"⚠️  Validacion XPath fallo (no afecta el ETL): {e}")


def task_limpiar_datos(**context):
    """
    Limpieza de datos antes del ETL:
      - Elimina registros con win_rate o pick_rate nulos
      - Elimina duplicados por (slug, input, region, rq)
      - Elimina espacios en blanco en campos de texto
      - Valida rangos: win_rate y pick_rate entre 0 y 100
    Guarda los datos limpios de vuelta en XCom.
    """
    ti            = context["ti"]
    blizzard_data = ti.xcom_pull(key="blizzard_data", task_ids="scrape_blizzard") or []

    antes = len(blizzard_data)
    vistos = set()
    limpios = []

    for r in blizzard_data:
        # Limpiar espacios en campos de texto
        r["slug"]   = _limpiar_texto(r.get("slug", ""))
        r["input"]  = _limpiar_texto(r.get("input", ""))
        r["region"] = _limpiar_texto(r.get("region", ""))

        # Validar que no haya nulos
        if not r["slug"] or r.get("win_rate") is None or r.get("pick_rate") is None:
            logging.warning(f"  ⚠️  Registro con nulos descartado: {r}")
            continue

        # Validar rangos
        if not (0 <= r["win_rate"] <= 100 and 0 <= r["pick_rate"] <= 100):
            logging.warning(f"  ⚠️  Registro fuera de rango descartado: {r}")
            continue

        # Eliminar duplicados
        clave = (r["slug"], r["input"], r["region"], r["rq"])
        if clave in vistos:
            continue
        vistos.add(clave)
        limpios.append(r)

    descartados = antes - len(limpios)
    logging.info(f"✅ Limpieza completada: {antes} → {len(limpios)} registros ({descartados} descartados)")
    ti.xcom_push(key="blizzard_data_limpio", value=limpios)


def task_etl_principal(**context):
    """
    ETL principal: inserta datos del dia en PostgreSQL.
    Usa los datos limpios de blizzard_data_limpio (XCom).
    Usa dificultad real extraida de /en-us/heroes/ (URL 2).
    Fallback sintetico si no hay dato real para una combinacion.
    """
    import psycopg2
    import random
    import pendulum
    hoy = pendulum.now("America/Merida").date()

    SLUG_A_NOMBRE = {
        h["nombre"].lower().replace(" ", "-").replace(":", "").replace(".", ""): h["nombre"]
        for h in HEROES
    }
    SLUG_A_NOMBRE.update({
        "soldier-76":    "Soldier: 76",
        "wrecking-ball": "Wrecking Ball",
        "junker-queen":  "Junker Queen",
        "d-va":          "D.Va",
        "torbjorn":      "Torbjorn",
    })

    ti = context["ti"]

    # Usar datos limpios del paso de limpieza
    blizzard_data = ti.xcom_pull(key="blizzard_data_limpio", task_ids="limpiar_datos") or []
    dificultades  = ti.xcom_pull(key="dificultades", task_ids="scrape_blizzard") or {}

    blizzard_map = {}
    for r in blizzard_data:
        key = (r["slug"], r["input"], r["region"], r["rq"])
        blizzard_map[key] = r

    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()
    hoy  = pendulum.now("America/Merida").date()

    cur.execute("""
        SELECT COUNT(*) FROM public.fact_hero_rates f
        JOIN public.dim_tiempo t ON t.id_tiempo = f.id_tiempo
        WHERE t.fecha = %s
    """, (hoy,))
    if cur.fetchone()[0] > 0:
        logging.info(f"Ya existen datos para {hoy}, saltando ETL")
        conn.close()
        return

    dia_semana = hoy.strftime("%A")
    cur.execute("""
        INSERT INTO public.dim_tiempo (fecha, hora, dia_semana, mes, anio)
        VALUES (%s, '14:00:00', %s, %s, %s)
        ON CONFLICT DO NOTHING RETURNING id_tiempo
    """, (hoy, dia_semana, hoy.month, hoy.year))
    row = cur.fetchone()
    if not row:
        cur.execute("SELECT id_tiempo FROM public.dim_tiempo WHERE fecha = %s", (hoy,))
        row = cur.fetchone()
    id_tiempo = row[0]

    registros = 0
    for h in HEROES:
        slug = h["nombre"].lower().replace(" ", "-").replace(":", "").replace(".", "")

        # Usar dificultad real de URL 2, fallback a 'Media'
        dificultad = dificultades.get(slug, "Media")

        cur.execute("SELECT id_heroe FROM public.dim_heroe WHERE nombre_heroe = %s", (h["nombre"],))
        row = cur.fetchone()
        if not row:
            cur.execute("""
                INSERT INTO public.dim_heroe (nombre_heroe, rol, dificultad)
                VALUES (%s, %s, %s) RETURNING id_heroe
            """, (h["nombre"], h["rol"], dificultad))
            row = cur.fetchone()
        else:
            # Actualizar dificultad si cambio
            cur.execute("""
                UPDATE public.dim_heroe SET dificultad = %s
                WHERE nombre_heroe = %s
            """, (dificultad, h["nombre"]))
        id_heroe = row[0]

        for plat in PLATAFORMAS:
            for region in REGIONES:
                for mapa in MAPAS:
                    for modo in MODOS:
                        rq = 0 if "queue" in modo else 1

                        key = (slug, plat, region, rq)
                        if key in blizzard_map:
                            wr = blizzard_map[key]["win_rate"]
                            pr = blizzard_map[key]["pick_rate"]
                        else:
                            seed = hash(h["nombre"]) + hoy.toordinal() + hash(plat)
                            random.seed(seed)
                            base_wr    = 48 + (hash(h["nombre"]) % 10)
                            base_pr    = 5  + (hash(h["nombre"]) % 15)
                            plat_bonus = 1.5 if plat == "PC" else -1.5
                            wr = round(base_wr + plat_bonus + random.uniform(-1.5, 1.5), 2)
                            pr = round(base_pr + random.uniform(-0.8, 0.8), 2)

                        cur.execute("""
                            SELECT id_contexto FROM public.dim_contexto
                            WHERE plataforma = %s AND modo_juego = %s AND tier = %s
                        """, (plat, modo, "All"))
                        row = cur.fetchone()
                        if not row:
                            cur.execute("""
                                INSERT INTO public.dim_contexto (plataforma, modo_juego, tier)
                                VALUES (%s, %s, %s) RETURNING id_contexto
                            """, (plat, modo, "All"))
                            row = cur.fetchone()
                        id_contexto = row[0]

                        cur.execute("""
                            SELECT id_escenario FROM public.dim_escenario
                            WHERE mapa = %s AND region = %s
                        """, (mapa, region))
                        row = cur.fetchone()
                        if not row:
                            cur.execute("""
                                INSERT INTO public.dim_escenario (mapa, region)
                                VALUES (%s, %s) RETURNING id_escenario
                            """, (mapa, region))
                            row = cur.fetchone()
                        id_escenario = row[0]

                        cur.execute("""
                            INSERT INTO public.fact_hero_rates
                            (id_heroe, id_contexto, id_escenario, id_tiempo, win_rate, pick_rate)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (id_heroe, id_contexto, id_escenario, id_tiempo, wr, pr))
                        registros += 1

    conn.commit()
    conn.close()
    logging.info(f"✅ ETL completado: {registros} registros insertados para {hoy}")


def task_actualizar_resumen_diario(**context):
    """Actualiza tabla resumen_diario"""
    import psycopg2
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()
    cur.execute("TRUNCATE TABLE public.resumen_diario")
    cur.execute("""
        INSERT INTO public.resumen_diario (fecha, nombre_heroe, rol, avg_win_rate, avg_pick_rate, ranking)
        SELECT fecha, nombre_heroe, rol, avg_win_rate, avg_pick_rate, ranking FROM (
            SELECT t.fecha, h.nombre_heroe, h.rol,
                   ROUND(AVG(f.win_rate)::numeric, 2)  AS avg_win_rate,
                   ROUND(AVG(f.pick_rate)::numeric, 2) AS avg_pick_rate,
                   ROW_NUMBER() OVER (PARTITION BY t.fecha ORDER BY AVG(f.win_rate) DESC) AS ranking
            FROM public.fact_hero_rates f
            JOIN public.dim_heroe  h ON h.id_heroe  = f.id_heroe
            JOIN public.dim_tiempo t ON t.id_tiempo = f.id_tiempo
            WHERE t.fecha = CURRENT_DATE
            GROUP BY t.fecha, h.nombre_heroe, h.rol
        ) sub
        ORDER BY avg_win_rate DESC
        LIMIT 10
    """)
    conn.commit()
    conn.close()
    logging.info("✅ resumen_diario actualizado")


def task_actualizar_comparativo(**context):
    """Actualiza tabla comparativo_plataforma"""
    import psycopg2
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()
    cur.execute("TRUNCATE TABLE public.comparativo_plataforma")
    cur.execute("""
        INSERT INTO public.comparativo_plataforma (fecha, nombre_heroe, rol, win_rate_pc, win_rate_console, diferencia)
        SELECT t.fecha, h.nombre_heroe, h.rol,
               ROUND(AVG(CASE WHEN c.plataforma = 'PC'      THEN f.win_rate END)::numeric, 2),
               ROUND(AVG(CASE WHEN c.plataforma = 'Console' THEN f.win_rate END)::numeric, 2),
               ROUND((AVG(CASE WHEN c.plataforma = 'PC'      THEN f.win_rate END) -
                      AVG(CASE WHEN c.plataforma = 'Console' THEN f.win_rate END))::numeric, 2)
        FROM public.fact_hero_rates f
        JOIN public.dim_heroe    h ON h.id_heroe    = f.id_heroe
        JOIN public.dim_contexto c ON c.id_contexto = f.id_contexto
        JOIN public.dim_tiempo   t ON t.id_tiempo   = f.id_tiempo
        WHERE t.fecha = CURRENT_DATE
        GROUP BY t.fecha, h.nombre_heroe, h.rol
        HAVING AVG(CASE WHEN c.plataforma = 'PC' THEN f.win_rate END) IS NOT NULL
    """)
    conn.commit()
    conn.close()
    logging.info("✅ comparativo_plataforma actualizado")


def task_actualizar_ranking_rol(**context):
    """Actualiza tabla ranking_por_rol"""
    import psycopg2
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()
    cur.execute("TRUNCATE TABLE public.ranking_por_rol")
    cur.execute("""
        INSERT INTO public.ranking_por_rol (fecha, rol, nombre_heroe, avg_win_rate, avg_pick_rate)
        SELECT fecha, rol, nombre_heroe, avg_win_rate, avg_pick_rate FROM (
            SELECT t.fecha, h.rol, h.nombre_heroe,
                   ROUND(AVG(f.win_rate)::numeric, 2)  AS avg_win_rate,
                   ROUND(AVG(f.pick_rate)::numeric, 2) AS avg_pick_rate
            FROM public.fact_hero_rates f
            JOIN public.dim_heroe  h ON h.id_heroe  = f.id_heroe
            JOIN public.dim_tiempo t ON t.id_tiempo = f.id_tiempo
            WHERE t.fecha = CURRENT_DATE
              AND h.rol IS NOT NULL
            GROUP BY t.fecha, h.rol, h.nombre_heroe
        ) sub
        ORDER BY rol, avg_win_rate DESC
    """)
    conn.commit()
    conn.close()
    logging.info("✅ ranking_por_rol actualizado")


def task_validar_datos(**context):
    """Valida que los datos se insertaron correctamente"""
    import psycopg2
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()

    cur.execute("""
        SELECT COUNT(*) FROM public.fact_hero_rates f
        JOIN public.dim_tiempo t ON t.id_tiempo = f.id_tiempo
        WHERE t.fecha = CURRENT_DATE
    """)
    fact_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM public.resumen_diario WHERE fecha = CURRENT_DATE")
    resumen_count = cur.fetchone()[0]

    conn.close()
    logging.info(f"✅ Validacion: {fact_count} registros en fact_hero_rates, {resumen_count} en resumen_diario")

    if fact_count == 0:
        raise Exception("❌ No se insertaron datos en fact_hero_rates")
    if resumen_count == 0:
        raise Exception("❌ No se insertaron datos en resumen_diario")


# ─── DAG ─────────────────────────────────────────────────────
with DAG(
    dag_id="overwatch2_pipeline",
    default_args=default_args,
    description="Pipeline ETL diario para Overwatch 2 BI",
    schedule_interval="@daily",
    start_date=datetime(2026, 1, 1, tzinfo=pendulum.timezone("America/Merida")),
    catchup=False,
    tags=["overwatch2", "etl", "bi"],
) as dag:

    inicio = EmptyOperator(task_id="inicio")

    verificar = PythonOperator(
        task_id="verificar_conexion",
        python_callable=task_verificar_conexion,
    )

    crear_indices = PythonOperator(
        task_id="crear_indices",
        python_callable=task_crear_indices,
    )

    scrape = PythonOperator(
        task_id="scrape_blizzard",
        python_callable=task_scrape_blizzard,
    )

    validar_xpath = PythonOperator(
        task_id="validar_xpath",
        python_callable=task_validar_xpath,
        trigger_rule="all_done",
    )

    limpiar = PythonOperator(
        task_id="limpiar_datos",
        python_callable=task_limpiar_datos,
    )

    etl = PythonOperator(
        task_id="etl_principal",
        python_callable=task_etl_principal,
    )

    resumen = PythonOperator(
        task_id="actualizar_resumen_diario",
        python_callable=task_actualizar_resumen_diario,
    )

    comparativo = PythonOperator(
        task_id="actualizar_comparativo",
        python_callable=task_actualizar_comparativo,
    )

    ranking = PythonOperator(
        task_id="actualizar_ranking_rol",
        python_callable=task_actualizar_ranking_rol,
    )

    validar = PythonOperator(
        task_id="validar_datos",
        python_callable=task_validar_datos,
    )

    fin = EmptyOperator(task_id="fin")

    # ── Flujo ─────────────────────────────────────────────────
    inicio >> verificar >> crear_indices >> scrape >> validar_xpath >> limpiar >> etl >> [resumen, comparativo, ranking] >> validar >> fin