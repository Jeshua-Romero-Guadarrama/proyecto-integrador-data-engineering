# 🛒 Pipeline de Datos End-to-End — Proyecto Integrador (Data Engineering)

Pipeline de datos **reproducible y de calidad** que ingesta ventas, las valida,
las transforma y persiste el resultado en **Parquet**, con orquestación (Airflow),
transformaciones SQL (dbt), procesamiento distribuido (PySpark), pruebas
automatizadas, CI/CD (GitHub Actions) y observabilidad (Prometheus + Grafana).

> Entrega Final — Coderhouse, Data Engineering. Autor: **Jeshua Romero Guadarrama**.

---

## 1. Descripción del proyecto

En un entorno profesional los datos llegan crudos, con errores potenciales y sin
estructura uniforme. Este proyecto simula ese escenario a escala accesible: toma un
dataset de **ventas** y lo recorre por el flujo canónico de un data engineer:

```
data → ingesta → validación → transformación → output (Parquet)
```

**Problema que resuelve:** convertir ventas transaccionales crudas en un dataset
analítico confiable de **ingreso total por producto y fecha**, listo para dashboards
o análisis, garantizando calidad de datos y reproducibilidad.

## 2. Dataset

CSV con una fila por línea de venta (`data/ventas.csv`, 1.000 filas generadas de
forma determinista con semilla fija):

| Columna           | Tipo   | Descripción                          |
|-------------------|--------|--------------------------------------|
| `fecha`           | date   | Fecha de la venta (2 meses de datos) |
| `producto_id`     | int    | Identificador del producto (101–108) |
| `cantidad`        | int    | Unidades vendidas (> 0)              |
| `precio_unitario` | float  | Precio unitario en la venta (> 0)    |

**Objetivo del pipeline:** calcular `ingreso_total = cantidad * precio_unitario` y
agregar la suma por `(fecha, producto_id)`.

## 3. Cómo ejecutar

Requisitos: Python 3.10+ (y Java 11+ sólo si querés correr PySpark).

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Generar el dataset de ejemplo (opcional: ya viene versionado)
python scripts/generar_datos.py --filas 1000

# 3. Ejecutar el pipeline end-to-end
python ejecutar_pipeline.py

# 4. Correr los tests
pytest

# 5. (Opcional) Transformaciones SQL con dbt
cd dbt/ventas && dbt build --profiles-dir .

# 6. (Opcional) Job de procesamiento distribuido con PySpark
python jobs/job_spark.py --entrada data/ventas.csv --salida output/spark_parquet
```

En Windows con PowerShell, definí primero `$env:PYTHONPATH = (Get-Location).Path`.

## 4. Resultado esperado

El pipeline genera en `output/`:

- `ingresos_por_producto_fecha.parquet` — **output principal** (columnar, comprimido).
- `ingresos_por_producto_fecha.csv` — misma data para inspección humana.
- `metrics/ventas_pipeline.prom` — métricas Prometheus de la corrida.

Ejemplo de salida (agregado por fecha y producto):

| fecha      | producto_id | unidades_vendidas | ingreso_total |
|------------|-------------|-------------------|---------------|
| 2023-01-01 | 101         | 1                 | 46.61         |
| 2023-01-01 | 103         | 23                | 4419.93       |

Corrida de referencia: **1.000 filas de entrada → 426 filas agregadas**,
ingreso total global **342.413,79**, 8/8 checks de calidad OK.

## 5. Estructura del proyecto

```
proyecto-integrador-dataeng/
├── ejecutar_pipeline.py     # Orquestador principal (ingesta→validación→transformación→carga→métricas)
├── config/pipeline.yml      # Configuración central (rutas, esquema, reglas)
├── data/                    # Datos de entrada (ventas.csv)
├── output/                  # Resultados (Parquet, CSV, métricas)
├── jobs/                    # Etapas del pipeline (ingesta, transformacion, validacion, carga, metricas, job_spark)
├── tests/                   # Pruebas automatizadas (pytest)
├── scripts/                 # Generador de datos y utilidades de evidencia
├── airflow/dags/            # DAG de orquestación
├── dbt/ventas/              # Proyecto dbt (modelos + tests SQL)
├── observability/           # Prometheus + Grafana (config y dashboard)
├── .github/workflows/       # CI/CD (GitHub Actions)
├── docs/evidence/           # Evidencia de ejecución (logs, resumen, preview)
├── docker-compose.yml       # Infra: Airflow + Prometheus + Grafana
├── Dockerfile               # Imagen del pipeline
├── Makefile                 # Atajos operativos
├── RUNBOOK.md               # Guía operativa
└── DOCUMENTACION.md         # Documento técnico end-to-end (para la entrega)
```

## 6. Decisiones técnicas

- **pandas como motor principal**: el volumen (miles de filas) entra holgado en
  memoria; pandas es simple, portable y sin dependencias pesadas → el pipeline
  corre en cualquier máquina. Se incluye además una implementación **PySpark**
  para demostrar el patrón distribuido cuando el volumen no entra en un nodo.
- **Parquet como formato de salida**: columnar, tipado y comprimido (snappy).
  Mucho más eficiente que CSV para consumo analítico posterior (dbt/Spark/BI).
- **Validación antes de transformar** ("fail fast"): si los datos no son
  confiables, el pipeline corta antes de producir un output engañoso.
- **Configuración declarativa** (`config/pipeline.yml`): rutas y reglas fuera del
  código → agregar una validación no requiere tocar la lógica.
- **dbt + DuckDB**: replica la transformación en SQL con tests declarativos, sin
  necesidad de una base de datos externa (adapter embebido).
- **Separación por etapas**: cada módulo (`ingest/transform/validate/load`) es
  independiente y testeable de forma aislada.

## 7. Documentación adicional

- 📘 [`DOCUMENTACION.md`](DOCUMENTACION.md) — documento técnico completo end-to-end
  (arquitectura, infra, orquestación, dbt, Spark, testing, CI/CD, observabilidad).
- 🛠️ [`RUNBOOK.md`](RUNBOOK.md) — guía operativa (ejecución, troubleshooting).
- 🧾 [`docs/evidence/`](docs/evidence/) — logs y resultados de ejecuciones reales.

## Licencia

MIT — ver [`LICENSE`](LICENSE).
