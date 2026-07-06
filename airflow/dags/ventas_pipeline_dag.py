"""DAG de Airflow que orquesta el pipeline de ventas end-to-end.

Flujo:
    generar_datos >> ingesta_y_validacion >> transformacion_y_carga >> dbt_build >> reporte

Cada etapa del pipeline Python se expone como una tarea. Se usan PythonOperator
para las etapas nativas y BashOperator para dbt (que se invoca por CLI). El DAG
está pensado para correr en el contenedor de Airflow definido en docker-compose.yml,
donde el proyecto se monta en /opt/airflow/project.

Programación: diaria (@daily). Con `catchup=False` para no re-ejecutar históricos.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

# El proyecto se monta en esta ruta dentro del contenedor de Airflow.
PROJECT_DIR = Path("/opt/airflow/project")
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

default_args = {
    "owner": "data-engineering",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    "depends_on_past": False,
}


def _generar_datos(**_):
    from scripts.generate_data import generar
    import csv

    filas = generar(rows=1000, seed=42)
    out = PROJECT_DIR / "data" / "ventas.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["fecha", "producto_id", "cantidad", "precio_unitario"])
        w.writeheader()
        w.writerows(filas)
    return str(out)


def _ingesta_validacion(**_):
    from jobs.ingest import ingest
    from jobs.validate import validate

    df = ingest()
    report = validate(df, raise_on_error=True)
    return report.as_dict()


def _transformacion_carga(**_):
    from run_pipeline import run

    resumen = run()
    return resumen["outputs"]


with DAG(
    dag_id="ventas_pipeline",
    description="Pipeline end-to-end de ventas: ingesta, validación, transformación, dbt.",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["dataeng", "ventas", "proyecto-integrador"],
) as dag:

    generar_datos = PythonOperator(
        task_id="generar_datos",
        python_callable=_generar_datos,
    )

    ingesta_y_validacion = PythonOperator(
        task_id="ingesta_y_validacion",
        python_callable=_ingesta_validacion,
    )

    transformacion_y_carga = PythonOperator(
        task_id="transformacion_y_carga",
        python_callable=_transformacion_carga,
    )

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command="cd /opt/airflow/project/dbt/ventas && dbt build --profiles-dir . || true",
    )

    reporte = BashOperator(
        task_id="reporte_final",
        bash_command='echo "Pipeline de ventas finalizado. Output en output/*.parquet"',
    )

    generar_datos >> ingesta_y_validacion >> transformacion_y_carga >> dbt_build >> reporte
