"""Etapa 4 — Carga: guardar el resultado en Parquet (y un CSV de yapa).

Elegí Parquet como formato principal porque es columnar, comprimido y guarda
los tipos, así que después se lee mucho más rápido y barato desde dbt, Spark o
una herramienta de BI. El CSV lo dejo nada más que para poder mirarlo a ojo.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from jobs.comunes import cargar_config, obtener_logger, resolver_ruta

log = obtener_logger("carga")


def guardar(datos: pd.DataFrame) -> dict[str, Path]:
    """Escribe el DataFrame final en Parquet y CSV y devuelve las rutas usadas."""
    rutas = cargar_config()["paths"]
    ruta_parquet = resolver_ruta(rutas["output_parquet"])
    ruta_csv = resolver_ruta(rutas["output_csv"])
    ruta_parquet.parent.mkdir(parents=True, exist_ok=True)

    # 'fecha' es un date de Python; pyarrow lo guarda como date32 en el Parquet.
    datos.to_parquet(ruta_parquet, engine="pyarrow", index=False, compression="snappy")
    datos.to_csv(ruta_csv, index=False)

    log.info("Resultado guardado en Parquet: %s (%d filas)", ruta_parquet, len(datos))
    log.info("Copia en CSV guardada en: %s", ruta_csv)
    return {"parquet": ruta_parquet, "csv": ruta_csv}
