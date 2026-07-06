"""Etapas del pipeline de ventas.

Separé cada etapa en su propio módulo para poder probarlas por separado:
    - ingesta       : leer el CSV y chequear que tenga la forma esperada.
    - transformacion: reglas de negocio (ingreso_total y agregado).
    - validacion    : reglas de calidad de datos.
    - carga         : guardar el resultado en Parquet / CSV.
    - comunes       : cosas compartidas (config, logging).
    - metricas      : métricas para Prometheus.
    - job_spark     : la misma lógica pero con PySpark (procesamiento distribuido).
"""
