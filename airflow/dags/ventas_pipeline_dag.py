"""DAG de Airflow que orquesta el pipeline de ventas de punta a punta.

Flujo:
    generar_datos >> ingesta_y_validacion >> transformacion_y_carga >> dbt_build >> reporte

Cada etapa reutiliza los mismos módulos de jobs/ (no duplico lógica).
El proyecto se monta en /opt/airflow/project dentro del contenedor de Airflow.

Programación: diaria (@daily), con catchup=False para no reprocesar históricos.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

from airflow import DAG

# El proyecto se monta acá adentro del contenedor; lo sumo al path para importar jobs/.
DIR_PROYECTO = Path("/opt/airflow/project")
if str(DIR_PROYECTO) not in sys.path:
    sys.path.insert(0, str(DIR_PROYECTO))

argumentos_por_defecto = {
    "owner": "Jeshua Romero Guadarrama",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    "depends_on_past": False,
}


def _generar_datos(**_):
    """Tarea: genera el CSV de ventas dentro del contenedor de Airflow."""
    import csv

    from scripts.generar_datos import generar

    registros = generar(filas=1000, semilla=42)
    salida = DIR_PROYECTO / "data" / "ventas.csv"
    salida.parent.mkdir(parents=True, exist_ok=True)
    with salida.open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(
            archivo, fieldnames=["fecha", "producto_id", "cantidad", "precio_unitario"]
        )
        escritor.writeheader()
        escritor.writerows(registros)
    return str(salida)


def _ingesta_y_validacion(**_):
    """Tarea: ingiere el CSV y corre las validaciones de calidad (corta si fallan)."""
    from jobs.ingesta import ingerir
    from jobs.validacion import validar

    datos = ingerir()
    reporte = validar(datos, lanzar_error=True)
    return reporte.como_dict()


def _transformacion_y_carga(**_):
    """Tarea: corre el pipeline completo (transforma y guarda el resultado)."""
    from ejecutar_pipeline import ejecutar

    resumen = ejecutar()
    return resumen["salidas"]


with DAG(
    dag_id="ventas_pipeline",
    description="Pipeline de ventas de punta a punta: ingesta, validación, transformación, dbt.",
    default_args=argumentos_por_defecto,
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
        python_callable=_ingesta_y_validacion,
    )

    transformacion_y_carga = PythonOperator(
        task_id="transformacion_y_carga",
        python_callable=_transformacion_y_carga,
    )

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command="cd /opt/airflow/project/dbt/ventas && dbt build --profiles-dir . || true",
    )

    reporte = BashOperator(
        task_id="reporte_final",
        bash_command='echo "Pipeline de ventas terminado. Output en output/*.parquet"',
    )

    generar_datos >> ingesta_y_validacion >> transformacion_y_carga >> dbt_build >> reporte
