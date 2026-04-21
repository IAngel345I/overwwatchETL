
import pg8000.dbapi
import logging
import random
from datetime import datetime, date, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

DB_CONFIG = {
    "host": "localhost", "port": 5432,
    "database": "overwatch2", "user": "postgres", "password": "planta40",
}

HEROES_BASE = [
    {"hero": "Ana",           "rol": "support"},
    {"hero": "Baptiste",      "rol": "support"},
    {"hero": "Brigitte",      "rol": "support"},
    {"hero": "Illari",        "rol": "support"},
    {"hero": "Juno",          "rol": "support"},
    {"hero": "Kiriko",        "rol": "support"},
    {"hero": "Lifeweaver",    "rol": "support"},
    {"hero": "Lucio",         "rol": "support"},
    {"hero": "Mercy",         "rol": "support"},
    {"hero": "Moira",         "rol": "support"},
    {"hero": "Zenyatta",      "rol": "support"},
    {"hero": "D.Va",          "rol": "tank"},
    {"hero": "Doomfist",      "rol": "tank"},
    {"hero": "Junker Queen",  "rol": "tank"},
    {"hero": "Mauga",         "rol": "tank"},
    {"hero": "Orisa",         "rol": "tank"},
    {"hero": "Ramattra",      "rol": "tank"},
    {"hero": "Reinhardt",     "rol": "tank"},
    {"hero": "Roadhog",       "rol": "tank"},
    {"hero": "Sigma",         "rol": "tank"},
    {"hero": "Winston",       "rol": "tank"},
    {"hero": "Wrecking Ball", "rol": "tank"},
    {"hero": "Zarya",         "rol": "tank"},
    {"hero": "Ashe",          "rol": "damage"},
    {"hero": "Bastion",       "rol": "damage"},
    {"hero": "Cassidy",       "rol": "damage"},
    {"hero": "Echo",          "rol": "damage"},
    {"hero": "Genji",         "rol": "damage"},
    {"hero": "Hanzo",         "rol": "damage"},
    {"hero": "Junkrat",       "rol": "damage"},
    {"hero": "Mei",           "rol": "damage"},
    {"hero": "Pharah",        "rol": "damage"},
    {"hero": "Reaper",        "rol": "damage"},
    {"hero": "Sojourn",       "rol": "damage"},
    {"hero": "Soldier: 76",   "rol": "damage"},
    {"hero": "Sombra",        "rol": "damage"},
    {"hero": "Symmetra",      "rol": "damage"},
    {"hero": "Torbjorn",      "rol": "damage"},
    {"hero": "Tracer",        "rol": "damage"},
    {"hero": "Venture",       "rol": "damage"},
    {"hero": "Widowmaker",    "rol": "damage"},
    # Nuevos heroes 2025-2026
    {"hero": "Hazard",        "rol": "tank"},
    {"hero": "Domina",        "rol": "tank"},
    {"hero": "Freja",         "rol": "damage"},
    {"hero": "Vendetta",      "rol": "damage"},
    {"hero": "Anran",         "rol": "damage"},
    {"hero": "Wuyang",        "rol": "support"},
    {"hero": "Mizuki",        "rol": "support"},
]

BASE_RATES = {
    "Ana":           (45.2, 10.5), "Baptiste":      (46.5, 4.6),
    "Brigitte":      (51.6, 3.0),  "Illari":        (53.1, 5.5),
    "Juno":          (51.6, 19.1), "Kiriko":        (44.7, 9.6),
    "Lifeweaver":    (45.5, 6.2),  "Lucio":         (52.3, 7.4),
    "Mercy":         (48.7, 19.6), "Moira":         (48.8, 12.9),
    "Zenyatta":      (54.5, 9.1),  "D.Va":          (50.1, 11.3),
    "Doomfist":      (49.3, 4.7),  "Junker Queen":  (51.3, 3.3),
    "Mauga":         (51.6, 5.4),  "Orisa":         (48.4, 8.3),
    "Ramattra":      (50.1, 7.1),  "Reinhardt":     (53.2, 8.1),
    "Roadhog":       (44.1, 5.5),  "Sigma":         (50.7, 5.0),
    "Winston":       (51.3, 2.1),  "Wrecking Ball": (49.3, 2.0),
    "Zarya":         (46.2, 2.5),  "Ashe":          (51.2, 11.1),
    "Bastion":       (52.1, 13.5), "Cassidy":       (49.6, 12.2),
    "Echo":          (48.9, 4.0),  "Genji":         (48.8, 6.5),
    "Hanzo":         (49.4, 5.7),  "Junkrat":       (49.7, 6.7),
    "Mei":           (52.9, 4.0),  "Pharah":        (48.7, 1.9),
    "Reaper":        (55.0, 9.0),  "Sojourn":       (46.1, 6.0),
    "Soldier: 76":   (51.7, 12.3), "Sombra":        (48.5, 5.7),
    "Symmetra":      (56.2, 3.0),  "Torbjorn":      (54.4, 3.1),
    "Tracer":        (51.2, 3.7),  "Venture":       (51.0, 2.0),
    "Widowmaker":    (45.3, 8.4),
    # Nuevos heroes 2025-2026
    "Hazard":        (52.4, 4.8),
    "Domina":        (57.1, 8.2),
    "Freja":         (50.8, 5.1),
    "Vendetta":      (55.3, 7.4),
    "Anran":         (49.6, 4.3),
    "Wuyang":        (51.2, 6.7),
    "Mizuki":        (50.4, 5.9),
}

MAP_MODIFIERS = {
    "Busan":          {"Lucio": (5.8, 6.8), "D.Va": (4.1, 5.4), "Tracer": (4.7, 3.4), "Moira": (3.2, 5.1), "Reinhardt": (-2.1, -1.8), "Bastion": (-3.2, 0.8)},
    "Ilios":          {"Lucio": (9.1, 9.4), "D.Va": (2.7, 3.1), "Moira": (1.8, 4.6), "Reaper": (1.8, 2.3), "Mercy": (-1.2, 1.5), "Reinhardt": (-1.4, 0.8)},
    "Nepal":          {"Reinhardt": (3.1, 2.3), "Reaper": (2.4, 3.6), "Torbjorn": (2.7, 2.7), "Symmetra": (2.1, 1.1), "Tracer": (-2.3, -1.4), "Widowmaker": (-3.1, -0.5)},
    "Oasis":          {"Lucio": (7.4, 5.7), "D.Va": (3.3, 2.4), "Tracer": (3.1, 2.3), "Moira": (0.8, 2.1), "Reinhardt": (-1.8, 0.5), "Bastion": (-1.4, 1.2)},
    "Samoa":          {"Lucio": (6.2, 7.1), "D.Va": (3.8, 4.2), "Winston": (4.1, 1.8), "Genji": (2.7, 2.4), "Reinhardt": (-2.4, -1.1), "Torbjorn": (-1.8, 0.9)},
    "Torre Lijiang":  {"Lucio": (8.3, 8.1), "Tracer": (5.2, 4.1), "Genji": (3.4, 3.2), "D.Va": (2.9, 3.7), "Reinhardt": (-3.1, -2.3), "Bastion": (-2.7, 1.1)},
    "Dorado":         {"Bastion": (3.8, 5.2), "Torbjorn": (3.2, 2.8), "Symmetra": (2.8, 1.4), "Reinhardt": (2.4, 1.9), "Winston": (-2.1, -0.7), "Tracer": (1.8, 1.2)},
    "Junkertown":     {"Bastion": (4.2, 5.8), "Torbjorn": (3.7, 3.4), "Pharah": (2.8, 1.6), "Widowmaker": (2.4, 2.1), "Lucio": (-2.8, -2.1), "D.Va": (-1.4, 0.8)},
    "La Habana":      {"Symmetra": (3.1, 1.8), "Bastion": (3.4, 4.9), "Reinhardt": (2.8, 2.4), "Mercy": (1.4, 2.8), "Tracer": (-1.7, -0.9), "Winston": (-2.3, -1.1)},
    "Ruta 66":        {"Widowmaker": (3.4, 3.2), "Ashe": (3.1, 2.8), "Bastion": (2.7, 4.1), "Torbjorn": (2.4, 2.6), "Lucio": (-3.2, -2.8), "D.Va": (-1.8, 0.6)},
    "Shambali":       {"Reinhardt": (3.2, 2.7), "Bastion": (2.8, 4.3), "Mercy": (1.7, 2.4), "Orisa": (2.4, 1.9), "Tracer": (-2.1, -1.3), "Genji": (-1.8, 0.4)},
    "Blizzard World": {"Reinhardt": (2.4, 2.1), "Ana": (1.8, 1.9), "Cassidy": (1.4, 2.3), "Mercy": (0.9, 1.8), "Tracer": (1.2, 0.7), "Bastion": (1.7, 2.4)},
    "Eichenwalde":    {"Reinhardt": (3.8, 3.4), "Ana": (2.1, 2.4), "Bastion": (2.4, 3.8), "Symmetra": (1.8, 0.9), "Tracer": (-1.4, -0.8), "Genji": (-0.9, 0.3)},
    "Hollywood":      {"Widowmaker": (2.8, 2.4), "Ashe": (2.4, 2.1), "Ana": (1.7, 1.8), "Cassidy": (1.4, 2.6), "Reinhardt": (1.2, 1.4), "Lucio": (-1.8, -0.7)},
    "King's Row":     {"Reinhardt": (4.1, 3.7), "Ana": (2.3, 2.8), "Bastion": (2.8, 4.2), "Zenyatta": (1.4, 1.8), "Tracer": (-0.9, -0.4), "D.Va": (1.2, 1.6)},
    "Midtown":        {"Widowmaker": (3.1, 2.7), "Ashe": (2.7, 2.4), "Cassidy": (2.1, 2.8), "Ana": (1.8, 2.1), "Lucio": (-1.4, -0.6), "Reinhardt": (1.4, 1.7)},
    "Numbani":        {"Tracer": (2.8, 2.1), "Genji": (2.4, 1.8), "Winston": (2.1, 1.4), "Ana": (1.7, 2.3), "Reinhardt": (-0.8, 0.4), "Bastion": (1.4, 2.1)},
    "Paraiso":        {"Pharah": (3.4, 2.8), "Ana": (2.1, 2.6), "Mercy": (1.8, 2.4), "Lucio": (1.4, 1.8), "Reinhardt": (-1.2, -0.3), "Bastion": (1.1, 1.8)},
    "Colosseo":       {"Tracer": (3.8, 3.2), "Lucio": (3.4, 3.7), "Winston": (3.1, 2.4), "Genji": (2.8, 2.6), "Reinhardt": (-2.8, -2.1), "Bastion": (-1.7, 1.1)},
    "Esperanca":      {"Tracer": (3.4, 2.8), "Lucio": (3.1, 3.4), "Genji": (2.7, 2.3), "Pharah": (2.4, 1.8), "Reinhardt": (-2.4, -1.8), "Torbjorn": (-1.4, 0.7)},
    "New Queen St":   {"Junker Queen": (4.2, 3.8), "Lucio": (3.2, 3.1), "Tracer": (3.1, 2.7), "Winston": (2.8, 2.1), "Reinhardt": (-2.1, -1.4), "Symmetra": (-1.8, 0.8)},
    "Runaapi":        {"Tracer": (3.7, 3.1), "Lucio": (3.4, 3.6), "Winston": (2.9, 2.2), "Genji": (2.6, 2.4), "Reinhardt": (-2.6, -1.9), "Bastion": (-1.9, 1.2)},
}

PLATFORM_MODIFIERS = {
    "PC": {
        "pick": 0.0, "win": 0.0,
        "hero_boost": {"Widowmaker": (2.4, 2.1), "Ashe": (1.8, 1.4), "Sojourn": (1.4, 1.1)},
    },
    "Console": {
        "pick": 1.2, "win": 0.8,
        "hero_boost": {"Reaper": (2.8, 2.4), "Soldier: 76": (3.1, 2.7), "Mercy": (3.4, 3.2),
                       "Bastion": (3.2, 2.8), "Torbjorn": (2.7, 2.1), "Widowmaker": (-2.8, -2.4)},
    },
}

REGION_MODIFIERS = {
    "Americas": {"pick": 0.0, "win": 0.0},
    "Asia":     {"pick": 0.0, "win": 0.0,
                 "hero_boost": {"Genji": (4.8, 2.7), "Hanzo": (2.7, 1.7), "Kiriko": (4.6, 3.2), "D.Va": (1.7, 0.8)}},
    "Europe":   {"pick": 0.0, "win": 0.0,
                 "hero_boost": {"Reinhardt": (1.6, 1.1), "Widowmaker": (1.4, 0.9), "Ana": (0.9, 0.7)}},
}

PLATAFORMAS = ["PC", "Console"]
MODOS       = ["Partida Rapida - Cola por Funcion", "Competitivo - Cola por Funcion"]
REGIONES    = ["Americas", "Asia", "Europe"]
MAPAS       = [
    "Busan", "Ilios", "Nepal", "Oasis", "Samoa", "Torre Lijiang",
    "Dorado", "Junkertown", "La Habana", "Ruta 66", "Shambali",
    "Blizzard World", "Eichenwalde", "Hollywood", "King's Row", "Midtown", "Numbani", "Paraiso",
    "Colosseo", "Esperanca", "New Queen St", "Runaapi",
]

DIAS_SEMANA = {
    0: "Lunes", 1: "Martes", 2: "Miercoles", 3: "Jueves",
    4: "Viernes", 5: "Sabado", 6: "Domingo"
}

# Tendencias acumuladas por heroe (simula cambios del meta dia a dia)
_tendencias = {}

def get_tendencia(hero: str, fecha: date) -> tuple:
    """Genera una tendencia acumulada por heroe usando la fecha como semilla."""
    random.seed(hash(hero) + fecha.toordinal())
    # Cada dia varia entre -1.5 y +1.5 en win_rate y -0.8 y +0.8 en pick_rate
    delta_win  = round(random.uniform(-1.5, 1.5), 1)
    delta_pick = round(random.uniform(-0.8, 0.8), 1)
    return delta_win, delta_pick

def calc_rates(hero, mapa, modo, plataforma, region, fecha: date):
    base_win, base_pick = BASE_RATES.get(hero, (50.0, 5.0))

    # Modificador de modo
    if modo == "Competitivo - Cola por Funcion":
        base_win  += 1.4
        base_pick += 1.8

    # Modificador de plataforma
    p = PLATFORM_MODIFIERS.get(plataforma, {"pick": 0, "win": 0, "hero_boost": {}})
    base_win  += p["win"]
    base_pick += p["pick"]
    if hero in p.get("hero_boost", {}):
        dw, dp = p["hero_boost"][hero]
        base_win  += dw
        base_pick += dp

    # Modificador de region
    r = REGION_MODIFIERS.get(region, {"pick": 0, "win": 0})
    if hero in r.get("hero_boost", {}):
        dw, dp = r["hero_boost"][hero]
        base_win  += dw
        base_pick += dp

    # Modificador de mapa
    if mapa in MAP_MODIFIERS and hero in MAP_MODIFIERS[mapa]:
        dw, dp = MAP_MODIFIERS[mapa][hero]
        base_win  += dw
        base_pick += dp

    # Variacion diaria aleatoria con tendencia acumulada
    dw, dp = get_tendencia(hero, fecha)
    base_win  += dw
    base_pick += dp

    base_win  = round(min(max(base_win,  30.0), 70.0), 1)
    base_pick = round(min(max(base_pick,  0.5), 40.0), 1)

    return base_win, base_pick


def connect_db():
    return pg8000.dbapi.connect(
        host=DB_CONFIG["host"], port=DB_CONFIG["port"],
        database=DB_CONFIG["database"], user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
    )

def get_or_create(cur, table, pk, cols, vals) -> int:
    where = " AND ".join(f"{c}=%s" for c in cols)
    cur.execute(f"SELECT {pk} FROM public.{table} WHERE {where}", vals)
    row = cur.fetchone()
    if row:
        return row[0]
    placeholders = ", ".join(["%s"] * len(vals))
    cur.execute(
        f"INSERT INTO public.{table} ({', '.join(cols)}) VALUES ({placeholders}) RETURNING {pk}",
        vals
    )
    return cur.fetchone()[0]

def get_or_create_tiempo(cur, fecha: date) -> int:
    hora    = "14:00:00"
    dia_sem = DIAS_SEMANA[fecha.weekday()]
    mes     = fecha.month
    anio    = fecha.year

    cur.execute(
        "SELECT id_tiempo FROM public.dim_tiempo WHERE fecha = %s AND hora = %s",
        (fecha, hora)
    )
    row = cur.fetchone()
    if row:
        return row[0]

    cur.execute(
        """INSERT INTO public.dim_tiempo (fecha, hora, dia_semana, mes, anio)
           VALUES (%s, %s, %s, %s, %s) RETURNING id_tiempo""",
        (fecha, hora, dia_sem, mes, anio)
    )
    return cur.fetchone()[0]


def run_etl_fecha(cur, conn, fecha: date, limite: int = 1000):
    """Corre el ETL para una fecha especifica con limite de registros."""
    log.info(f"Procesando fecha: {fecha}")
    id_tiempo = get_or_create_tiempo(cur, fecha)
    conn.commit()

    # Verificar si ya tiene registros esta fecha
    cur.execute("SELECT COUNT(*) FROM public.fact_hero_rates WHERE id_tiempo = %s", (id_tiempo,))
    existentes = cur.fetchone()[0]
    if existentes >= limite:
        log.info(f"  Fecha {fecha} ya tiene {existentes} registros, saltando.")
        return 0

    total = 0
    combinaciones = [
        (plat, modo, reg, mapa)
        for plat in PLATAFORMAS
        for modo in MODOS
        for reg in REGIONES
        for mapa in MAPAS
    ]
    random.seed(fecha.toordinal())
    random.shuffle(combinaciones)

    for plataforma, modo, region, mapa in combinaciones:
        if total >= limite:
            break

        id_ctx = get_or_create(cur, "dim_contexto", "id_contexto",
                               ["plataforma", "modo_juego", "tier"],
                               (plataforma, modo, "All"))

        id_esc = get_or_create(cur, "dim_escenario", "id_escenario",
                               ["region", "mapa"], (region, mapa))

        for h in HEROES_BASE:
            if total >= limite:
                break

            hero = h["hero"]
            id_h = get_or_create(cur, "dim_heroe", "id_heroe", ["nombre_heroe"], (hero,))
            cur.execute(
                "UPDATE public.dim_heroe SET rol=%s WHERE id_heroe=%s AND rol IS NULL",
                (h["rol"], id_h)
            )

            win, pick = calc_rates(hero, mapa, modo, plataforma, region, fecha)

            cur.execute("""
                INSERT INTO public.fact_hero_rates
                    (id_heroe, id_contexto, id_escenario, id_tiempo, win_rate, pick_rate)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id_heroe, id_contexto, id_escenario, id_tiempo)
                DO UPDATE SET
                    win_rate  = EXCLUDED.win_rate,
                    pick_rate = EXCLUDED.pick_rate
            """, (id_h, id_ctx, id_esc, id_tiempo, win, pick))
            total += 1

        conn.commit()

    log.info(f"  {total} registros guardados para {fecha}")
    return total


def run_etl():
    """ETL principal - corre para hoy con 1000 registros."""
    log.info("Iniciando ETL diario...")
    conn = connect_db()
    cur  = conn.cursor()
    try:
        total = run_etl_fecha(cur, conn, date.today(), limite=1000)
        log.info(f"ETL completado: {total} registros para {date.today()}")
    except Exception as e:
        conn.rollback()
        log.error(f"Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def run_etl_historico():
    """Genera historial desde 20 de febrero hasta ayer con 1000 registros por dia."""
    log.info("Generando historial desde 2026-02-20 hasta hoy...")
    conn  = connect_db()
    cur   = conn.cursor()
    inicio = date(2026, 2, 20)
    hoy    = date.today()
    fecha  = inicio
    total_global = 0

    try:
        while fecha <= hoy:
            total = run_etl_fecha(cur, conn, fecha, limite=1000)
            total_global += total
            fecha += timedelta(days=1)

        log.info(f"Historico completado: {total_global} registros desde {inicio} hasta {hoy}")
    except Exception as e:
        conn.rollback()
        log.error(f"Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    run_etl_historico()