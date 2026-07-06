"""Fixtures que comparten los tests (datasets chiquitos armados a mano)."""
from __future__ import annotations

import datetime as dt

import pandas as pd
import pytest


@pytest.fixture
def ventas_validas() -> pd.DataFrame:
    """Un dataset limpio con dos productos en dos fechas."""
    return pd.DataFrame(
        {
            "fecha": [
                dt.date(2023, 1, 1),
                dt.date(2023, 1, 1),
                dt.date(2023, 1, 1),
                dt.date(2023, 1, 2),
            ],
            "producto_id": [101, 101, 102, 101],
            "cantidad": [2, 3, 1, 4],
            "precio_unitario": [40.0, 40.0, 25.0, 40.0],
        }
    )


@pytest.fixture
def ventas_con_negativos() -> pd.DataFrame:
    """Trae una cantidad negativa a propósito, para que falle la validación."""
    return pd.DataFrame(
        {
            "fecha": [dt.date(2023, 1, 1), dt.date(2023, 1, 2)],
            "producto_id": [101, 102],
            "cantidad": [5, -2],
            "precio_unitario": [40.0, 25.0],
        }
    )


@pytest.fixture
def ventas_con_nulos() -> pd.DataFrame:
    """Trae un precio nulo a propósito, para que falle la validación."""
    return pd.DataFrame(
        {
            "fecha": [dt.date(2023, 1, 1), dt.date(2023, 1, 2)],
            "producto_id": [101, 102],
            "cantidad": [5, 3],
            "precio_unitario": [40.0, None],
        }
    )
