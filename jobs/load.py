"""Etapa 4 — Carga: persistencia del resultado en Parquet (y CSV de apoyo).

Parquet es el formato preferido por ser columnar, comprimido y tipado, ideal
para consumo analítico posterior (dashboards, dbt, Spark). Se genera además un
CSV para inspección humana rápida.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from jobs.common import get_logger, load_config, resolve

log = get_logger("load")


def load(df: pd.DataFrame) -> dict[str, Path]:
    """Persiste el DataFrame final en Parquet y CSV. Devuelve las rutas escritas."""
    cfg = load_config()["paths"]
    parquet_path = resolve(cfg["output_parquet"])
    csv_path = resolve(cfg["output_csv"])
    parquet_path.parent.mkdir(parents=True, exist_ok=True)

    # 'fecha' es date de Python; pyarrow lo mapea a tipo date32 en Parquet.
    df.to_parquet(parquet_path, engine="pyarrow", index=False, compression="snappy")
    df.to_csv(csv_path, index=False)

    log.info("Resultado escrito en Parquet: %s (%d filas)", parquet_path, len(df))
    log.info("Copia CSV escrita en: %s", csv_path)
    return {"parquet": parquet_path, "csv": csv_path}
