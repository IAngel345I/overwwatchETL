http://127.0.0.1:8000/docs#

http://localhost:8080

cd "D:\overwwatchETL\overwatch_docker"
docker-compose up -d

docker-compose up -d → levanta todo
Espera a que Airflow corra el pipeline
Verifica en http://localhost:8080 que todo esté verde
Ve a Docker Desktop → stop a overwatch_docker

LIMPIEZA DE CAHCHE DE AIRFLOE:
docker exec -it airflow_webserver rm -f /opt/airflow/airflow-webserver.pid
docker restart airflow_webserver

# Overwatch 2 BI v2 — Hero Rates Analytics

## Proposito del Analisis BI

**Pregunta de negocio central:**
> ¿Que heroes dominan el meta de Overwatch 2 segun plataforma, region, nivel competitivo y mapa, y como evoluciona ese dominio parche a parche?

### Casos de uso concretos:

**1. Deteccion de heroes overpowered**
Cruza win_rate alto + pick_rate alto para identificar heroes que dominan el meta
y que probablemente seran nerfeados en el siguiente parche.

**2. Analisis de meta por plataforma (PC vs Consola)**
Los jugadores de consola tienen limitaciones de aim — esto cambia radicalmente
que heroes son efectivos. El modelo permite comparar ambos contextos.

**3. Diferencias regionales**
Americas, Asia y Europa tienen culturas de juego distintas. Ciertos heroes
son mas populares o efectivos segun la region, lo cual refleja distintos estilos de juego.

**4. Evolucion del meta por parche**
Al guardar un snapshot diario, se puede trazar la linea de tiempo de como
un nerfeo o buff impacta el win_rate de un heroe a lo largo del tiempo.

**5. Analisis por tier competitivo**
Un heroe puede ser muy fuerte en niveles bajos (Bronze/Gold) pero debil en
Grandmaster. Esto ayuda a jugadores a elegir heroes segun su nivel real.

---

## Modelo de Datos

```
dim_heroe         dim_contexto          dim_escenario
-----------       ----------------      ---------------
id_heroe    <--+  id_contexto    <--+   id_escenario  <--+
nombre_heroe    |  plataforma       |   region            |
rol             |  modo_juego       |   mapa              |
dificultad      |  tier             |                     |
                |                   |                     |
                +---fact_hero_rates-+---------------------+
                       id
                       id_heroe
                       id_contexto
                       id_escenario
                       pick_rate
                       win_rate
                       fecha_snapshot
```

**Por que este modelo estrella:**
- `dim_heroe` → quien juega
- `dim_contexto` → como y en que nivel juega
- `dim_escenario` → donde juega (mapa + region)
- `fact_hero_rates` → que tan bien le va (pick + win rate)

---

## Archivos

| Archivo | Descripcion |
|---------|-------------|
| `schema.sql` | Crear las tablas en PostgreSQL |
| `etl_v2.py` | ETL que extrae datos de Blizzard |
| `api_v2.py` | API REST con FastAPI |

---

## Setup

### 1. Crear tablas en PostgreSQL
Abre pgAdmin, conéctate a tu base `overwtach2` y ejecuta `schema.sql`.

### 2. Instalar dependencias
```bash
pip install fastapi uvicorn requests pg8000
```

### 3. Correr la API
```bash
cd d:\overwwatchETL\files
python -m uvicorn api_v2:app --reload --port 8000
```

### 4. Ejecutar el ETL
Abre http://localhost:8000/docs y ejecuta `POST /etl/run`

---

## Endpoints de Analisis

| Endpoint | Descripcion |
|----------|-------------|
| `GET /rates/latest` | Ultimo snapshot completo (filtrable) |
| `GET /rates/top-winrate` | Top heroes por win rate |
| `GET /rates/top-pickrate` | Top heroes por pick rate |
| `GET /rates/heroe/{nombre}` | Historial de un heroe |
| `GET /rates/comparar-regiones` | Un heroe en Americas vs Asia vs Europa |

---

## Ejemplos de preguntas que responde este BI

- ¿Quien es el heroe con mayor win rate en Consola, Americas, nivel Diamond?
- ¿Como cambio el win rate de Ana tras el ultimo parche?
- ¿Que heroes son mas picked en Asia vs Americas?
- ¿Hay diferencia entre PC y Consola para los Tanks?
- ¿Que heroes de Support dominan en Grandmaster?