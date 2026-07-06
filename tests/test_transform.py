"""Tests de la etapa de transformación (reglas de negocio)."""
from __future__ import annotations

import datetime as dt

from jobs.transform import add_ingreso_total, aggregate_por_producto_fecha, transform


def test_ingreso_total_es_cantidad_por_precio(ventas_validas):
    out = add_ingreso_total(ventas_validas)
    assert "ingreso_total" in out.columns
    # fila 0: 2 * 40 = 80
    assert out.loc[0, "ingreso_total"] == 80.0
    # fila 2: 1 * 25 = 25
    assert out.loc[2, "ingreso_total"] == 25.0


def test_agregacion_suma_por_producto_y_fecha(ventas_validas):
    resultado = transform(ventas_validas)
    # Combinaciones esperadas: (1/1,101), (1/1,102), (1/2,101) -> 3 filas
    assert len(resultado) == 3

    fila = resultado[
        (resultado["fecha"] == dt.date(2023, 1, 1))
        & (resultado["producto_id"] == 101)
    ].iloc[0]
    # (2*40) + (3*40) = 200
    assert fila["ingreso_total"] == 200.0
    assert fila["unidades_vendidas"] == 5


def test_ingreso_total_global_se_conserva(ventas_validas):
    con_ingreso = add_ingreso_total(ventas_validas)
    agregado = aggregate_por_producto_fecha(con_ingreso)
    # La suma de ingreso no cambia al agregar (sólo se reorganiza).
    assert round(con_ingreso["ingreso_total"].sum(), 2) == round(
        agregado["ingreso_total"].sum(), 2
    )


def test_columnas_de_salida(ventas_validas):
    resultado = transform(ventas_validas)
    assert list(resultado.columns) == [
        "fecha",
        "producto_id",
        "unidades_vendidas",
        "ingreso_total",
    ]
