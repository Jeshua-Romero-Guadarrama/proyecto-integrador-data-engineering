"""Test end-to-end del pipeline completo sobre el dataset de ejemplo."""
from __future__ import annotations

from pathlib import Path

from run_pipeline import run


def test_pipeline_completo_genera_output():
    resumen = run()
    assert resumen["status"] == "success"
    assert resumen["rows_in"] > 0
    assert resumen["rows_out"] > 0
    assert resumen["ingreso_total"] > 0
    assert resumen["validation"]["ok"] is True

    parquet = Path(resumen["outputs"]["parquet"])
    assert parquet.exists()
    assert parquet.stat().st_size > 0


def test_output_es_consistente():
    """rows_out <= rows_in (la agregación no puede crear filas)."""
    resumen = run()
    assert resumen["rows_out"] <= resumen["rows_in"]
