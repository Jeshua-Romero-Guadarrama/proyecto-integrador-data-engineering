"""Utilidades compartidas: carga de configuración y logging estructurado."""
from __future__ import annotations

import logging
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

# Raíz del proyecto (dos niveles arriba de este archivo: jobs/common.py -> proyecto/).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "pipeline.yml"


@lru_cache(maxsize=1)
def load_config(path: str | os.PathLike | None = None) -> dict[str, Any]:
    """Carga la configuración YAML del pipeline (cacheada)."""
    cfg_path = Path(path) if path else DEFAULT_CONFIG
    with cfg_path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def resolve(relative: str) -> Path:
    """Resuelve una ruta relativa respecto de la raíz del proyecto."""
    p = Path(relative)
    return p if p.is_absolute() else PROJECT_ROOT / p


def get_logger(name: str = "pipeline") -> logging.Logger:
    """Devuelve un logger con formato consistente (nivel configurable por LOG_LEVEL)."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger
