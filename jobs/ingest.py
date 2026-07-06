"""Etapa 1 — Ingesta: lectura del CSV de entrada y validación estructural.

Responsabilidad: abrir el archivo, cargarlo en memoria (pandas), confirmar que
las columnas requeridas existen y castear los tipos según la configuración.
No aplica reglas de negocio ni de calidad (eso es de transform/validate).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from jobs.common import get_logger, load_config, resolve

log = get_logger("ingest")


class SchemaError(ValueError):
    """Se lanza cuando el archivo de entrada no cumple el esquema esperado."""


def ingest(input_path: str | Path | None = None) -> pd.DataFrame:
    """Lee el CSV de ventas y devuelve un DataFrame tipado.

    Args:
        input_path: ruta al CSV. Si es None se usa la de config/pipeline.yml.

    Returns:
        DataFrame con columnas [fecha, producto_id, cantidad, precio_unitario].

    Raises:
        FileNotFoundError: si el archivo no existe.
        SchemaError: si faltan columnas requeridas.
    """
    cfg = load_config()
    path = Path(input_path) if input_path else resolve(cfg["paths"]["input_csv"])

    if not path.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo de entrada: {path}. "
            f"Generalo con: python scripts/generate_data.py"
        )

    log.info("Leyendo archivo de entrada: %s", path)
    df = pd.read_csv(path)

    requeridas = cfg["validation"]["columnas_requeridas"]
    faltantes = [c for c in requeridas if c not in df.columns]
    if faltantes:
        raise SchemaError(f"Columnas requeridas faltantes: {faltantes}")

    # Casteo de tipos según el esquema declarado.
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce").dt.date
    df["producto_id"] = pd.to_numeric(df["producto_id"], errors="coerce").astype("Int64")
    df["cantidad"] = pd.to_numeric(df["cantidad"], errors="coerce").astype("Int64")
    df["precio_unitario"] = pd.to_numeric(df["precio_unitario"], errors="coerce")

    log.info("Ingesta completada: %d filas, %d columnas", len(df), df.shape[1])
    return df


if __name__ == "__main__":
    frame = ingest()
    print(frame.head())
    print(f"\nTotal de registros: {len(frame)}")
