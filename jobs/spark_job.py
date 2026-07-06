"""Procesamiento distribuido con PySpark (implementación alternativa a pandas).

Misma lógica de negocio que jobs/transform.py pero usando la API de DataFrames de
Spark, pensada para escalar a volúmenes grandes en un clúster. Se ejecuta en modo
`local[*]` para desarrollo/CI y en un clúster real cambiando `spark.master`.

Uso:
    python jobs/spark_job.py --input data/ventas.csv --output output/spark_parquet

Casos de uso:
    - Volúmenes que no entran en memoria de un solo nodo.
    - Lecturas/escrituras particionadas en un data lake (S3/HDFS/GCS).
    - Integración con Airflow vía SparkSubmitOperator.
"""
from __future__ import annotations

import argparse


def run(input_path: str, output_path: str) -> None:
    from pyspark.sql import SparkSession
    from pyspark.sql import functions as F

    spark = (
        SparkSession.builder.appName("ventas_pipeline_spark")
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    df = (
        spark.read.option("header", True)
        .option("inferSchema", True)
        .csv(input_path)
    )

    # Regla de negocio: ingreso_total = cantidad * precio_unitario.
    con_ingreso = df.withColumn(
        "ingreso_total", F.round(F.col("cantidad") * F.col("precio_unitario"), 2)
    )

    resultado = (
        con_ingreso.groupBy("fecha", "producto_id")
        .agg(
            F.sum("cantidad").alias("unidades_vendidas"),
            F.round(F.sum("ingreso_total"), 2).alias("ingreso_total"),
        )
        .orderBy("fecha", "producto_id")
    )

    resultado.show(10, truncate=False)
    print(f"[spark_job] filas agregadas: {resultado.count()}")

    # Escritura Parquet particionada por fecha (patrón típico de data lake).
    # En clúster / Linux / Docker se usa el writer nativo de Spark. En Windows
    # sin winutils.exe (HADOOP_HOME) el committer de Hadoop falla, por lo que se
    # cae con elegancia a una escritura vía pandas + pyarrow (mismo resultado).
    try:
        resultado.write.mode("overwrite").partitionBy("fecha").parquet(output_path)
        print(f"[spark_job] Parquet particionado escrito por Spark en: {output_path}")
    except Exception as exc:  # noqa: BLE001
        print(f"[spark_job] Writer nativo no disponible ({type(exc).__name__}); "
              f"usando fallback pandas -> pyarrow.")
        import os

        os.makedirs(output_path, exist_ok=True)
        destino = os.path.join(output_path, "ingresos_spark.parquet")
        resultado.toPandas().to_parquet(destino, engine="pyarrow", index=False)
        print(f"[spark_job] Parquet escrito (fallback) en: {destino}")

    spark.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Job PySpark de agregación de ventas")
    parser.add_argument("--input", default="data/ventas.csv")
    parser.add_argument("--output", default="output/spark_parquet")
    args = parser.parse_args()
    run(args.input, args.output)


if __name__ == "__main__":
    main()
