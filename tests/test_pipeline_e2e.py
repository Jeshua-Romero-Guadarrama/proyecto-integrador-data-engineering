"""Test de punta a punta del pipeline completo sobre el dataset de ejemplo."""
from __future__ import annotations

from pathlib import Path

from ejecutar_pipeline import ejecutar


def test_pipeline_completo_genera_output():
    resumen = ejecutar()
    assert resumen["estado"] == "exito"
    assert resumen["filas_entrada"] > 0
    assert resumen["filas_salida"] > 0
    assert resumen["ingreso_total"] > 0
    assert resumen["validacion"]["ok"] is True

    parquet = Path(resumen["salidas"]["parquet"])
    assert parquet.exists()
    assert parquet.stat().st_size > 0


def test_output_es_consistente():
    """filas_salida <= filas_entrada (agrupar nunca puede crear filas)."""
    resumen = ejecutar()
    assert resumen["filas_salida"] <= resumen["filas_entrada"]
