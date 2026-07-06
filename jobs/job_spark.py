"""Versión con PySpark de la misma transformación (procesamiento distribuido).

Hace exactamente lo mismo que jobs/transformacion.py pero con la API de Spark,
pensada para cuando el volumen no entra en la memoria de una sola máquina.
Lo corro en modo local[*] para desarrollo y CI; para un clúster real basta con
cambiar spark.master.

Uso:
    python jobs/job_spark.py --entrada data/ventas.csv --salida output/spark_parquet
"""
from __future__ import annotations

import argparse


def ejecutar(ruta_entrada: str, ruta_salida: str) -> None:
    """Levanta Spark, calcula el agregado de ingresos y lo guarda en Parquet."""
    from pyspark.sql import SparkSession
    from pyspark.sql import functions as F

    spark = (
        SparkSession.builder.appName("ventas_pipeline_spark")
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    datos = (
        spark.read.option("header", True)
        .option("inferSchema", True)
        .csv(ruta_entrada)
    )

    # Misma regla de negocio: ingreso_total = cantidad * precio_unitario.
    con_ingreso = datos.withColumn(
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
    print(f"[job_spark] filas agregadas: {resultado.count()}")

    # En un clúster o en Linux/Docker uso el writer nativo de Spark, que además
    # particiona por fecha (patrón típico de data lake). En Windows sin
    # winutils.exe el committer de Hadoop falla, así que caigo con elegancia a
    # una escritura vía pandas + pyarrow, que da el mismo resultado.
    try:
        resultado.write.mode("overwrite").partitionBy("fecha").parquet(ruta_salida)
        print(f"[job_spark] Parquet particionado escrito por Spark en: {ruta_salida}")
    except Exception as error:  # noqa: BLE001
        print(f"[job_spark] Writer nativo no disponible ({type(error).__name__}); "
              f"uso el respaldo pandas -> pyarrow.")
        import os

        os.makedirs(ruta_salida, exist_ok=True)
        destino = os.path.join(ruta_salida, "ingresos_spark.parquet")
        resultado.toPandas().to_parquet(destino, engine="pyarrow", index=False)
        print(f"[job_spark] Parquet escrito (respaldo) en: {destino}")

    spark.stop()


def main() -> None:
    """Lee los argumentos de la CLI y dispara el job de Spark."""
    parser = argparse.ArgumentParser(description="Job PySpark de agregación de ventas")
    parser.add_argument("--entrada", default="data/ventas.csv")
    parser.add_argument("--salida", default="output/spark_parquet")
    args = parser.parse_args()
    ejecutar(args.entrada, args.salida)


if __name__ == "__main__":
    main()
