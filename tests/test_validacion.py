"""Tests de la etapa de validación de calidad."""
from __future__ import annotations

import pytest

from jobs.validacion import ErrorCalidadDatos, validar


def test_datos_validos_pasan(ventas_validas):
    reporte = validar(ventas_validas, lanzar_error=False)
    assert reporte.ok
    d = reporte.como_dict()
    assert d["aprobados"] == d["total"]


def test_cantidad_negativa_falla(ventas_con_negativos):
    reporte = validar(ventas_con_negativos, lanzar_error=False)
    assert not reporte.ok
    fallidos = [c["chequeo"] for c in reporte.chequeos if not c["ok"]]
    assert "positivos::cantidad" in fallidos


def test_valor_nulo_falla(ventas_con_nulos):
    reporte = validar(ventas_con_nulos, lanzar_error=False)
    assert not reporte.ok
    fallidos = [c["chequeo"] for c in reporte.chequeos if not c["ok"]]
    assert "no_nulos::precio_unitario" in fallidos


def test_lanzar_error_tira_excepcion(ventas_con_negativos):
    with pytest.raises(ErrorCalidadDatos):
        validar(ventas_con_negativos, lanzar_error=True)


def test_estructura_del_reporte(ventas_validas):
    d = validar(ventas_validas, lanzar_error=False).como_dict()
    assert set(d.keys()) == {"ok", "total", "aprobados", "chequeos"}
    assert d["total"] >= 4  # al menos las 4 familias de reglas
