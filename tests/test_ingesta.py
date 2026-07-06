"""Tests de la etapa de ingesta (lectura y chequeo estructural)."""
from __future__ import annotations

import pandas as pd
import pytest

from jobs.ingesta import ErrorEsquema, ingerir


def _escribir_csv(ruta, contenido: str) -> None:
    ruta.write_text(contenido, encoding="utf-8")


def test_ingesta_lee_csv_valido(tmp_path):
    csv = tmp_path / "ventas.csv"
    _escribir_csv(
        csv,
        "fecha,producto_id,cantidad,precio_unitario\n"
        "2023-01-01,101,2,40.0\n"
        "2023-01-01,102,1,25.0\n",
    )
    datos = ingerir(csv)
    assert len(datos) == 2
    assert list(datos.columns) == ["fecha", "producto_id", "cantidad", "precio_unitario"]
    assert pd.api.types.is_float_dtype(datos["precio_unitario"])


def test_archivo_inexistente_lanza_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        ingerir(tmp_path / "no_existe.csv")


def test_columna_faltante_lanza_error_esquema(tmp_path):
    csv = tmp_path / "malo.csv"
    _escribir_csv(csv, "fecha,producto_id,cantidad\n2023-01-01,101,2\n")
    with pytest.raises(ErrorEsquema):
        ingerir(csv)


def test_dataset_real_de_ejemplo():
    """El CSV versionado en data/ tiene que ingerirse sin errores."""
    datos = ingerir()  # usa la ruta por defecto del config
    assert len(datos) > 0
    assert datos["cantidad"].min() >= 1
