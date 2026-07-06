# 📘 Documentación Técnica End-to-End — Pipeline de Ventas

**Proyecto Integrador Final — Data Engineering (Coderhouse)**
Autor: **Jeshua Romero Guadarrama** · Repositorio: *(ver enlace de GitHub en la entrega)*

> Este documento centraliza y evidencia todo el pipeline end-to-end. Está
> estructurado según los criterios de la rúbrica. Cada sección incluye
> descripción, decisiones de diseño y evidencia de funcionamiento.
> **Para la entrega en Google Docs:** copiar este contenido a un Google Doc con
> acceso público, o compartir el repositorio de GitHub (ambos aceptados).

---

## Índice

1. [Arquitectura y justificación técnica](#1-arquitectura-y-justificación-técnica)
2. [Infraestructura](#2-infraestructura)
3. [Orquestación (Airflow)](#3-orquestación-airflow)
4. [Transformaciones (dbt)](#4-transformaciones-dbt)
5. [Procesamiento distribuido (PySpark)](#5-procesamiento-distribuido-pyspark)
6. [Datos de ejemplo](#6-datos-de-ejemplo)
7. [Pruebas automatizadas](#7-pruebas-automatizadas)
8. [CI/CD](#8-cicd)
9. [Observabilidad](#9-observabilidad)
10. [Runbook](#10-runbook)
11. [Documentación técnica adicional](#11-documentación-técnica-adicional)
12. [Guía de demo](#12-guía-de-demo)
13. [Evidencia de ejecución](#13-evidencia-de-ejecución)
14. [Calidad del código](#14-calidad-del-código)

---

## 1. Arquitectura y justificación técnica

### 1.1 Diseño del sistema

El pipeline sigue el patrón canónico de ingeniería de datos, con etapas
desacopladas y una única fuente de configuración:

```
                    ┌────────────────────────────────────────────────┐
                    │            config/pipeline.yml                  │
                    │   (rutas · esquema · reglas de validación)      │
                    └────────────────────────────────────────────────┘
                                      │ (leído por todas las etapas)
                                      ▼
   data/ventas.csv ──► [1] INGESTA ──► [2] VALIDACIÓN ──► [3] TRANSFORMACIÓN ──► [4] CARGA ──► output/*.parquet
      (fuente)          ingest.py       validate.py         transform.py          load.py       (+ CSV)
                                          │ (fail-fast)                                │
                                          ▼                                            ▼
                                   DataQualityError                        [5] MÉTRICAS (metrics.py)
                                   (corta el pipeline)                      output/metrics/*.prom

   Orquestación:   Airflow DAG  ──►  encadena las etapas + dbt (diario, con reintentos)
   Transform SQL:  dbt (DuckDB) ──►  stg_ventas → fct_ingresos  (con tests declarativos)
   Distribuido:    PySpark job  ──►  misma lógica a escala de clúster
   Observabilidad: Pushgateway → Prometheus → Grafana
```

### 1.2 Decisiones tomadas y trade-offs

| Decisión | Alternativa | Justificación / trade-off |
|----------|-------------|---------------------------|
| **pandas** como motor principal | PySpark / DuckDB | El volumen entra en memoria; pandas es simple y portable (corre sin infra). Se incluye PySpark aparte para el caso distribuido. |
| **Parquet** (snappy) de salida | CSV / JSON | Columnar, tipado y comprimido → lecturas analíticas más rápidas y baratas. CSV se mantiene sólo para inspección humana. |
| **Validación previa** (fail-fast) | Validar al final / no validar | Evita persistir outputs engañosos; detecta problemas de calidad lo antes posible. |
| **Config declarativa** (YAML) | Constantes en código | Cambiar reglas/rutas sin tocar lógica → menos riesgo de regresión. |
| **dbt + DuckDB** | dbt + Postgres/Snowflake | Reproduce la transformación en SQL con tests, sin base externa → runnable en cualquier lado y en CI. |
| **Etapas desacopladas** | Un único script monolítico | Testeabilidad y mantenibilidad: cada etapa se prueba de forma aislada. |
| **Degradación elegante en Spark** | Fallar en Windows | El job cae al writer pandas si falta `winutils`, sin perder el resultado. |

**Principio rector (del enunciado):** *no buscamos complejidad innecesaria*. Cada
herramienta "avanzada" (Airflow, dbt, Spark, Prometheus) está presente porque
mapea a un criterio de la rúbrica y aporta valor real, pero el **núcleo del
pipeline funciona con un solo comando** (`python run_pipeline.py`) sin dependencias
de infraestructura.

---

## 2. Infraestructura

Los servicios se definen en `docker-compose.yml` (anexo). Incluye:

- **PostgreSQL** — metastore de Airflow.
- **Airflow** (webserver + scheduler, LocalExecutor) — orquestación.
- **Pushgateway** — recibe las métricas del pipeline batch.
- **Prometheus** — scrapea el Pushgateway.
- **Grafana** — dashboard aprovisionado automáticamente.

Puertos: Airflow `8080`, Grafana `3000`, Prometheus `9090`, Pushgateway `9091`.

```yaml
# Fragmento de docker-compose.yml (servicios de observabilidad)
  prometheus:
    image: prom/prometheus:v2.54.1
    volumes:
      - ./observability/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    ports: ["9090:9090"]
  grafana:
    image: grafana/grafana:11.2.0
    volumes:
      - ./observability/grafana/provisioning:/etc/grafana/provisioning:ro
      - ./observability/grafana/dashboards:/var/lib/grafana/dashboards:ro
    ports: ["3000:3000"]
```

La imagen del pipeline (`Dockerfile`) parte de `python:3.12-slim`, instala Java
(para PySpark) y las dependencias, y por defecto genera datos y ejecuta el pipeline.

Levantar todo: `docker compose up -d`.

---

## 3. Orquestación (Airflow)

DAG: `airflow/dags/ventas_pipeline_dag.py` (`dag_id = ventas_pipeline`).

- **Programación**: `@daily`, `catchup=False`, `retries=2` (backoff 2 min).
- **Tareas** (en orden):
  1. `generar_datos` — produce `data/ventas.csv` (determinista).
  2. `ingesta_y_validacion` — lee y aplica las reglas de calidad (falla si no pasan).
  3. `transformacion_y_carga` — calcula ingreso, agrega y escribe Parquet/CSV.
  4. `dbt_build` — corre modelos + tests de dbt.
  5. `reporte_final` — cierre/log.

```
generar_datos → ingesta_y_validacion → transformacion_y_carga → dbt_build → reporte_final
```

Lógica de ejecución: cada `PythonOperator` reutiliza los mismos módulos de `jobs/`
(sin duplicar lógica). El proyecto se monta en `/opt/airflow/project` y se agrega a
`PYTHONPATH`. La captura de la UI de Airflow (grafo del DAG en verde) se incluye en
`docs/evidence/` al desplegar con Docker.

---

## 4. Transformaciones (dbt)

Proyecto: `dbt/ventas/` · Adapter: **DuckDB** (embebido, sin base externa).

**Modelos** (flujo de datos):

```
read_csv_auto(data/ventas.csv)
        │
        ▼
  stg_ventas (view)   ── normaliza tipos + calcula ingreso_linea por venta
        │
        ▼
  fct_ingresos (table) ── SUM(ingreso) agrupado por (fecha, producto_id)
```

- `models/staging/stg_ventas.sql` — staging: castea tipos y calcula
  `ingreso_linea = cantidad * precio_unitario`.
- `models/marts/fct_ingresos.sql` — tabla de hechos: ingreso total por
  `(fecha, producto_id)`. **Equivale en SQL al output de `jobs/transform.py`**, lo
  que permite validación cruzada entre ambas implementaciones.

**Tests definidos** (14 en total, todos declarativos):

- `not_null` sobre columnas clave de ambos modelos.
- `positivo` (test genérico propio, `tests/generic/positivo.sql`) sobre `cantidad`,
  `precio_unitario`, `unidades_vendidas`, `ingreso_total`.
- `assert_grilla_unica` (test singular) — unicidad del par `(fecha, producto_id)`.

Ejecución: `cd dbt/ventas && dbt build --profiles-dir .` →
**`PASS=16 WARN=0 ERROR=0`** (2 modelos + 14 tests). Ver log en
`docs/evidence/03_dbt_build.log`.

---

## 5. Procesamiento distribuido (PySpark)

Job: `jobs/spark_job.py`. Reimplementa la lógica de negocio con la API de
DataFrames de Spark, ejecutable en `local[*]` (dev/CI) o en un clúster real
cambiando `spark.master`.

**Lógica implementada:**

```python
con_ingreso = df.withColumn("ingreso_total",
                            F.round(F.col("cantidad") * F.col("precio_unitario"), 2))
resultado = (con_ingreso.groupBy("fecha", "producto_id")
             .agg(F.sum("cantidad").alias("unidades_vendidas"),
                  F.round(F.sum("ingreso_total"), 2).alias("ingreso_total")))
resultado.write.mode("overwrite").partitionBy("fecha").parquet(output_path)
```

**Casos de uso:** volúmenes que no entran en memoria de un nodo, escritura
particionada en un data lake (S3/HDFS/GCS), integración con Airflow vía
`SparkSubmitOperator`.

**Resultado verificado:** el job produce **426 filas agregadas**, idénticas al
pipeline pandas (validación cruzada). En Windows sin `winutils.exe` el committer de
Hadoop no está disponible, por lo que el job **cae con elegancia** a una escritura
`toPandas() → pyarrow` (mismo resultado); en Linux/Docker usa el writer nativo
particionado. Ver `docs/evidence/04_spark_job.log`.

---

## 6. Datos de ejemplo

Fuente: `data/ventas.csv` (1.000 filas), generado por `scripts/generate_data.py`
con **semilla fija (42)** ⇒ reproducible.

**Estructura:**

| Columna | Tipo | Rango / dominio |
|---------|------|-----------------|
| `fecha` | date | 2023-01-01 … 2023-03-01 (60 días) |
| `producto_id` | int | 101–108 (catálogo de 8 productos) |
| `cantidad` | int | 1–12 |
| `precio_unitario` | float | precio de lista ±5% (promos) |

Muestra:

```
fecha,producto_id,cantidad,precio_unitario
2023-01-01,101,1,46.61
2023-01-01,103,7,190.43
2023-01-01,104,3,33.11
```

Se puede ajustar el volumen con `--rows N`. Los datos vienen versionados en el repo
para que sea clonable y ejecutable sin pasos extra.

---

## 7. Pruebas automatizadas

Framework: **pytest**. Suite en `tests/` (15 tests, todos en verde).

**Estrategia de testing** (pirámide):

- **Unitarias por etapa**:
  - `test_ingest.py` — lectura OK, archivo inexistente, columna faltante, dataset real.
  - `test_transform.py` — `ingreso_total` correcto, agregación por clave, conservación
    del total, columnas de salida.
  - `test_validate.py` — datos válidos pasan; negativos y nulos fallan; excepción con
    `raise_on_error`; estructura del reporte.
- **End-to-end**: `test_pipeline_e2e.py` — corre `run_pipeline.run()` y verifica
  éxito, existencia del Parquet e invariante `rows_out <= rows_in`.
- **Fixtures** (`conftest.py`): datasets sintéticos válidos, con negativos y con nulos.

Ejemplo representativo (invariante de negocio):

```python
def test_agregacion_suma_por_producto_y_fecha(ventas_validas):
    resultado = transform(ventas_validas)
    fila = resultado[(resultado.fecha == date(2023,1,1)) &
                     (resultado.producto_id == 101)].iloc[0]
    assert fila["ingreso_total"] == 200.0     # (2*40) + (3*40)
    assert fila["unidades_vendidas"] == 5
```

Ejecución: `pytest` → **15 passed**. Ver `docs/evidence/02_pytest.log`.

---

## 8. CI/CD

Pipeline: `.github/workflows/ci.yml` (GitHub Actions), disparado en `push` y
`pull_request` a `main`.

**Etapas y validaciones:**

1. Checkout + setup de Python 3.12 y Java 17.
2. Instalar dependencias (`requirements.txt`).
3. **Lint** (`ruff`) — informativo.
4. **Generar** el dataset de ejemplo.
5. **Tests** (`pytest -v`) — bloquea el merge si fallan.
6. **Pipeline end-to-end** (`run_pipeline.py`).
7. **dbt build** — modelos + tests SQL.
8. **Publicar artefactos** (`output/` y `docs/evidence/`).

**Flujo esperado:** un PR que rompa una regla de negocio o de calidad hace fallar
`pytest`/`dbt` y **bloquea el merge**, garantizando que `main` siempre tenga un
pipeline verde y reproducible.

---

## 9. Observabilidad

**Instrumentación** (`jobs/metrics.py`): al terminar cada corrida se emiten métricas
en dos destinos:

1. **Textfile** `output/metrics/ventas_pipeline.prom` (siempre; sin red).
2. **Pushgateway** si `PUSHGATEWAY_URL` está definido (dentro de Docker).

**Métricas expuestas:**

| Métrica | Significado |
|---------|-------------|
| `ventas_pipeline_last_success_timestamp` | Marca de tiempo de la última corrida OK |
| `ventas_pipeline_duration_seconds` | Duración de la corrida |
| `ventas_pipeline_rows_in` / `_rows_out` | Filas de entrada / salida |
| `ventas_pipeline_ingreso_total` | Ingreso total procesado |
| `ventas_pipeline_checks_passed` / `_failed` | Resultado de la validación de calidad |

**Logs**: logging estructurado con nivel configurable (`LOG_LEVEL`), formato
uniforme por etapa (`ingest`, `validate`, `transform`, `load`, `metrics`).

**Dashboards**: Grafana con datasource Prometheus aprovisionado y dashboard
"Pipeline de Ventas" (`observability/grafana/dashboards/pipeline_dashboard.json`):
paneles de última corrida, duración, ingreso, checks pass/fail y filas in/out.

**Diagnóstico**: `_checks_failed > 0` o ausencia de `last_success_timestamp`
recientes indican un problema; el runbook detalla la respuesta.

---

## 10. Runbook

Guía operativa completa en [`RUNBOOK.md`](RUNBOOK.md): puesta en marcha, ejecución
programada con Airflow, observabilidad, verificación de corridas, tabla de
troubleshooting, mantenimiento y rollback.

Resumen de operación diaria:

```bash
python run_pipeline.py            # ejecutar
cat docs/evidence/run_summary.json # verificar status=success y validation.ok=true
```

---

## 11. Documentación técnica adicional

- **Contrato de datos**: esquema y reglas en `config/pipeline.yml` (única fuente de
  verdad para ingesta y validación).
- **Idempotencia**: el pipeline sobrescribe el output de forma determinista; misma
  entrada ⇒ misma salida (semilla fija).
- **Extensibilidad**: agregar una fuente = nuevo módulo en `jobs/`; agregar una
  regla = una línea en el YAML; agregar un test = un archivo en `tests/`.
- **Portabilidad**: núcleo sin dependencias de infra; los componentes "pesados"
  (Airflow/Spark/Grafana) son opcionales y viven en Docker.

---

## 12. Guía de demo

Pasos para reproducir el funcionamiento (5 minutos, sin Docker):

```bash
# 1. Clonar
git clone <URL-del-repo> && cd proyecto-integrador-dataeng

# 2. Instalar
pip install -r requirements.txt

# 3. (Opcional) regenerar datos
python scripts/generate_data.py --rows 1000

# 4. Ejecutar el pipeline  → observar el log de etapas y el resumen final
python run_pipeline.py

# 5. Ver el output
#    output/ingresos_por_producto_fecha.parquet  (principal)
#    output/ingresos_por_producto_fecha.csv       (inspección)

# 6. Correr los tests
pytest

# 7. Transformaciones SQL con dbt
cd dbt/ventas && dbt build --profiles-dir .
```

Demo con infraestructura completa: `docker compose up -d`, luego Airflow (`:8080`)
para disparar el DAG y Grafana (`:3000`) para ver las métricas.

---

## 13. Evidencia de ejecución

Todas las corridas reales se capturan en `docs/evidence/`:

| Archivo | Contenido |
|---------|-----------|
| `01_run_pipeline.log` | Log completo del pipeline end-to-end |
| `02_pytest.log` | 15 tests — **15 passed** |
| `03_dbt_build.log` | dbt — **PASS=16 (2 modelos + 14 tests)** |
| `04_spark_job.log` | Job PySpark — 426 filas agregadas |
| `05_output_preview.md` | Esquema Parquet + muestra + métricas de negocio |
| `run_summary.json` | Resumen estructurado de la corrida |

**Resultados de referencia (corrida real):**

- Entrada: **1.000 filas** → Salida: **426 filas** agregadas.
- **Ingreso total global: 342.413,79**.
- Validación de calidad: **8/8 checks OK**.
- Tests: **15/15 passed** · dbt: **16/16 PASS**.
- Consistencia cruzada: pandas y PySpark producen las **mismas 426 filas**.

---

## 14. Calidad del código

**Buenas prácticas aplicadas:**

- **Separación de responsabilidades**: una etapa = un módulo, con una función
  pública clara y docstring explicativo.
- **Type hints** y `from __future__ import annotations` en todo el código.
- **Configuración externa** (YAML) en vez de valores hardcodeados.
- **Errores de dominio explícitos**: `SchemaError`, `DataQualityError` (fallos
  legibles y accionables).
- **Logging** estructurado en lugar de `print`.
- **Fail-fast**: validar antes de transformar.
- **Idempotencia** y **reproducibilidad** (semilla fija).
- **Tests** unitarios + e2e; **CI** que los ejecuta en cada cambio.
- **Comentarios que explican el "por qué"**, no el "qué".

Fragmento representativo (transformación — corazón del pipeline):

```python
def add_ingreso_total(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega la columna calculada ingreso_total = cantidad * precio_unitario."""
    out = df.copy()
    out["ingreso_total"] = (out["cantidad"] * out["precio_unitario"]).round(2)
    return out

def aggregate_por_producto_fecha(df: pd.DataFrame) -> pd.DataFrame:
    """Agrupa por (fecha, producto_id) y suma ingreso_total."""
    agg = (df.groupby(["fecha", "producto_id"], as_index=False)
             .agg(unidades_vendidas=("cantidad", "sum"),
                  ingreso_total=("ingreso_total", "sum"))
             .sort_values(["fecha", "producto_id"]).reset_index(drop=True))
    agg["ingreso_total"] = agg["ingreso_total"].round(2)
    return agg
```

Fragmento representativo (validación declarativa dirigida por configuración):

```python
for col in cfg["positivos"]:              # reglas definidas en pipeline.yml
    no_positivos = int((df[col] <= 0).sum())
    report.add(f"positivos::{col}", no_positivos == 0, f"<=0 => {no_positivos}")
```

---

*Fin del documento. Repositorio con el código completo, evidencia y CI en GitHub.*
