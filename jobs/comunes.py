"""Utilidades que comparten todas las etapas: config y logging.

Puse acá lo que se repetía en varios módulos (leer el YAML, armar rutas,
crear el logger) para no copiar y pegar lo mismo en cada archivo.
"""
from __future__ import annotations

import logging
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

# Raíz del proyecto: subo dos niveles desde jobs/comunes.py hasta la carpeta raíz.
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
CONFIG_POR_DEFECTO = RAIZ_PROYECTO / "config" / "pipeline.yml"


@lru_cache(maxsize=1)
def cargar_config(ruta: str | os.PathLike | None = None) -> dict[str, Any]:
    """Lee la configuración del pipeline desde el YAML.

    La cacheo con lru_cache porque se pide en varios lugares y el archivo no
    cambia durante la corrida; así lo leo del disco una sola vez.
    """
    ruta_cfg = Path(ruta) if ruta else CONFIG_POR_DEFECTO
    with ruta_cfg.open("r", encoding="utf-8") as archivo:
        return yaml.safe_load(archivo)


def resolver_ruta(relativa: str) -> Path:
    """Convierte una ruta relativa (del YAML) en una ruta absoluta desde la raíz."""
    ruta = Path(relativa)
    return ruta if ruta.is_absolute() else RAIZ_PROYECTO / ruta


def obtener_logger(nombre: str = "pipeline") -> logging.Logger:
    """Devuelve un logger ya configurado con un formato uniforme.

    El nivel se puede cambiar con la variable de entorno LOG_LEVEL (por defecto
    INFO). Evito agregar handlers de más chequeando si ya tiene alguno.
    """
    logger = logging.getLogger(nombre)
    if logger.handlers:
        return logger
    nivel = os.getenv("LOG_LEVEL", "INFO").upper()
    manejador = logging.StreamHandler(sys.stdout)
    manejador.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(manejador)
    logger.setLevel(nivel)
    logger.propagate = False
    return logger
