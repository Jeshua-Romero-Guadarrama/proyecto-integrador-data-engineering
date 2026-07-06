"""Etapa 1 — Ingesta: leer el CSV y revisar que tenga la forma esperada.

Acá solo abro el archivo, lo cargo con pandas y me aseguro de que estén las
columnas que necesito, casteando los tipos. Las reglas de negocio y de calidad
las dejo para las etapas de transformación y validación.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from jobs.comunes import cargar_config, obtener_logger, resolver_ruta

log = obtener_logger("ingesta")


class ErrorEsquema(ValueError):
    """La lanzo cuando el CSV no tiene las columnas que el pipeline espera."""


def ingerir(ruta_entrada: str | Path | None = None) -> pd.DataFrame:
    """Lee el CSV de ventas y devuelve un DataFrame ya tipado.

    Si no le paso ruta, uso la que está en config/pipeline.yml. Corto con un
    error claro si el archivo no existe o si le faltan columnas obligatorias.
    """
    config = cargar_config()
    ruta = Path(ruta_entrada) if ruta_entrada else resolver_ruta(config["paths"]["input_csv"])

    if not ruta.exists():
        raise FileNotFoundError(
            f"No encontré el archivo de entrada: {ruta}. "
            f"Generalo con: python scripts/generar_datos.py"
        )

    log.info("Leyendo archivo de entrada: %s", ruta)
    datos = pd.read_csv(ruta)

    columnas_requeridas = config["validation"]["columnas_requeridas"]
    faltantes = [columna for columna in columnas_requeridas if columna not in datos.columns]
    if faltantes:
        raise ErrorEsquema(f"Faltan columnas obligatorias: {faltantes}")

    # Fuerzo los tipos según el esquema. Uso 'coerce' para que un valor raro
    # quede como NaN/NaT y lo detecte después la etapa de validación.
    datos["fecha"] = pd.to_datetime(datos["fecha"], errors="coerce").dt.date
    datos["producto_id"] = pd.to_numeric(datos["producto_id"], errors="coerce").astype("Int64")
    datos["cantidad"] = pd.to_numeric(datos["cantidad"], errors="coerce").astype("Int64")
    datos["precio_unitario"] = pd.to_numeric(datos["precio_unitario"], errors="coerce")

    log.info("Ingesta lista: %d filas, %d columnas", len(datos), datos.shape[1])
    return datos


if __name__ == "__main__":
    tabla = ingerir()
    print(tabla.head())
    print(f"\nTotal de registros: {len(tabla)}")
