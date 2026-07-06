"""Tests de la etapa de ingesta (lectura y validación estructural)."""
from __future__ import annotations

import pandas as pd
import pytest

from jobs.ingest import SchemaError, ingest


def _escribir_csv(path, contenido: str) -> None:
    path.write_text(contenido, encoding="utf-8")


def test_ingesta_lee_csv_valido(tmp_path):
    csv = tmp_path / "ventas.csv"
    _escribir_csv(
        csv,
        "fecha,producto_id,cantidad,precio_unitario\n"
        "2023-01-01,101,2,40.0\n"
        "2023-01-01,102,1,25.0\n",
    )
    df = ingest(csv)
    assert len(df) == 2
    assert list(df.columns) == ["fecha", "producto_id", "cantidad", "precio_unitario"]
    assert pd.api.types.is_float_dtype(df["precio_unitario"])


def test_archivo_inexistente_lanza_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        ingest(tmp_path / "no_existe.csv")


def test_columna_faltante_lanza_schema_error(tmp_path):
    csv = tmp_path / "malo.csv"
    _escribir_csv(csv, "fecha,producto_id,cantidad\n2023-01-01,101,2\n")
    with pytest.raises(SchemaError):
        ingest(csv)


def test_dataset_real_de_ejemplo():
    """El dataset versionado en data/ debe ingerirse sin errores."""
    df = ingest()  # usa la ruta por defecto de config
    assert len(df) > 0
    assert df["cantidad"].min() >= 1
