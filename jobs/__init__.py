"""Paquete con las etapas del pipeline de ventas.

Cada etapa es un módulo independiente y testeable:
    - ingest    : lectura y validación estructural del CSV de entrada.
    - transform : reglas de negocio (ingreso_total y agregación).
    - validate  : reglas de calidad de datos.
    - load      : persistencia del resultado (Parquet / CSV).
    - common    : utilidades compartidas (config, logging).
    - metrics   : instrumentación Prometheus.
    - spark_job : implementación alternativa con PySpark (procesamiento distribuido).
"""
