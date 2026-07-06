"""Tests de la etapa de transformación (reglas de negocio)."""
from __future__ import annotations

import datetime as dt

from jobs.transformacion import (
    agregar_ingreso_total,
    agrupar_por_producto_fecha,
    transformar,
)


def test_ingreso_total_es_cantidad_por_precio(ventas_validas):
    """La columna ingreso_total tiene que ser cantidad * precio_unitario."""
    salida = agregar_ingreso_total(ventas_validas)
    assert "ingreso_total" in salida.columns
    # fila 0: 2 * 40 = 80
    assert salida.loc[0, "ingreso_total"] == 80.0
    # fila 2: 1 * 25 = 25
    assert salida.loc[2, "ingreso_total"] == 25.0


def test_agregado_suma_por_producto_y_fecha(ventas_validas):
    """El agrupado suma el ingreso y las unidades por cada par (fecha, producto)."""
    resultado = transformar(ventas_validas)
    # Combinaciones esperadas: (1/1,101), (1/1,102), (1/2,101) -> 3 filas
    assert len(resultado) == 3

    fila = resultado[
        (resultado["fecha"] == dt.date(2023, 1, 1))
        & (resultado["producto_id"] == 101)
    ].iloc[0]
    # (2*40) + (3*40) = 200
    assert fila["ingreso_total"] == 200.0
    assert fila["unidades_vendidas"] == 5


def test_el_ingreso_global_no_cambia_al_agrupar(ventas_validas):
    """Agrupar no debe alterar la suma total del ingreso, solo reorganizarla."""
    con_ingreso = agregar_ingreso_total(ventas_validas)
    agregado = agrupar_por_producto_fecha(con_ingreso)
    # Agrupar solo reorganiza: la suma total del ingreso tiene que ser la misma.
    assert round(con_ingreso["ingreso_total"].sum(), 2) == round(
        agregado["ingreso_total"].sum(), 2
    )


def test_columnas_de_salida(ventas_validas):
    """El resultado final expone exactamente las columnas esperadas y en orden."""
    resultado = transformar(ventas_validas)
    assert list(resultado.columns) == [
        "fecha",
        "producto_id",
        "unidades_vendidas",
        "ingreso_total",
    ]
