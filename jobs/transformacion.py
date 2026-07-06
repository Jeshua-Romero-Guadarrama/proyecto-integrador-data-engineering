"""Etapa 2 — Transformación: la lógica de negocio del proyecto.

Son dos pasos nada más:
    1. calcular ingreso_total = cantidad * precio_unitario por cada venta;
    2. sumar ese ingreso agrupando por fecha y producto.

El resultado es una fila por combinación de fecha y producto.
"""
from __future__ import annotations

import pandas as pd

from jobs.comunes import obtener_logger

log = obtener_logger("transformacion")


def agregar_ingreso_total(datos: pd.DataFrame) -> pd.DataFrame:
    """Suma la columna ingreso_total = cantidad * precio_unitario.

    Trabajo sobre una copia para no pisar el DataFrame original que me llega.
    """
    salida = datos.copy()
    salida["ingreso_total"] = (salida["cantidad"] * salida["precio_unitario"]).round(2)
    return salida


def agrupar_por_producto_fecha(datos: pd.DataFrame) -> pd.DataFrame:
    """Agrupa por (fecha, producto_id) y suma ingreso y unidades.

    Ordeno el resultado por fecha y producto para que la salida sea estable
    y fácil de leer (y de comparar entre corridas).
    """
    agregado = (
        datos.groupby(["fecha", "producto_id"], as_index=False)
        .agg(
            unidades_vendidas=("cantidad", "sum"),
            ingreso_total=("ingreso_total", "sum"),
        )
        .sort_values(["fecha", "producto_id"])
        .reset_index(drop=True)
    )
    agregado["ingreso_total"] = agregado["ingreso_total"].round(2)
    return agregado


def transformar(datos: pd.DataFrame) -> pd.DataFrame:
    """Encadena los dos pasos: primero el ingreso por venta y después el agregado."""
    log.info("Transformando %d filas de entrada", len(datos))
    con_ingreso = agregar_ingreso_total(datos)
    resultado = agrupar_por_producto_fecha(con_ingreso)
    log.info(
        "Transformación lista: %d filas agregadas (ingreso total global=%.2f)",
        len(resultado),
        resultado["ingreso_total"].sum(),
    )
    return resultado
