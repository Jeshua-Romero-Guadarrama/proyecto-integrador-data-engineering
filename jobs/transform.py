"""Etapa 2 — Transformación: reglas de negocio del pipeline.

Corazón del proyecto. Aplica:
    1. ingreso_total = cantidad * precio_unitario
    2. Agregación (suma de ingreso_total) por (fecha, producto_id).

Output final: un registro por combinación fecha/producto con el ingreso total.
"""
from __future__ import annotations

import pandas as pd

from jobs.common import get_logger

log = get_logger("transform")


def add_ingreso_total(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega la columna calculada ingreso_total = cantidad * precio_unitario."""
    out = df.copy()
    out["ingreso_total"] = (out["cantidad"] * out["precio_unitario"]).round(2)
    return out


def aggregate_por_producto_fecha(df: pd.DataFrame) -> pd.DataFrame:
    """Agrupa por (fecha, producto_id) y suma ingreso_total.

    Devuelve columnas: fecha, producto_id, unidades_vendidas, ingreso_total.
    """
    agg = (
        df.groupby(["fecha", "producto_id"], as_index=False)
        .agg(
            unidades_vendidas=("cantidad", "sum"),
            ingreso_total=("ingreso_total", "sum"),
        )
        .sort_values(["fecha", "producto_id"])
        .reset_index(drop=True)
    )
    agg["ingreso_total"] = agg["ingreso_total"].round(2)
    return agg


def transform(df: pd.DataFrame) -> pd.DataFrame:
    """Pipeline de transformación completo (calcula ingreso y agrega)."""
    log.info("Transformando %d filas de entrada", len(df))
    con_ingreso = add_ingreso_total(df)
    resultado = aggregate_por_producto_fecha(con_ingreso)
    log.info(
        "Transformación completada: %d filas agregadas (ingreso total global=%.2f)",
        len(resultado),
        resultado["ingreso_total"].sum(),
    )
    return resultado
