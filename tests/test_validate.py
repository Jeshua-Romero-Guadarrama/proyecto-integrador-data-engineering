"""Tests de la etapa de validación de calidad de datos."""
from __future__ import annotations

import pytest

from jobs.validate import DataQualityError, validate


def test_datos_validos_pasan(ventas_validas):
    report = validate(ventas_validas, raise_on_error=False)
    assert report.ok
    d = report.as_dict()
    assert d["passed"] == d["total"]


def test_cantidad_negativa_falla(ventas_con_negativos):
    report = validate(ventas_con_negativos, raise_on_error=False)
    assert not report.ok
    fallidos = [c["check"] for c in report.checks if not c["passed"]]
    assert "positivos::cantidad" in fallidos


def test_valor_nulo_falla(ventas_con_nulos):
    report = validate(ventas_con_nulos, raise_on_error=False)
    assert not report.ok
    fallidos = [c["check"] for c in report.checks if not c["passed"]]
    assert "no_nulos::precio_unitario" in fallidos


def test_raise_on_error_lanza_excepcion(ventas_con_negativos):
    with pytest.raises(DataQualityError):
        validate(ventas_con_negativos, raise_on_error=True)


def test_reporte_estructura(ventas_validas):
    d = validate(ventas_validas, raise_on_error=False).as_dict()
    assert set(d.keys()) == {"ok", "total", "passed", "checks"}
    assert d["total"] >= 4  # al menos las 4 familias de reglas
