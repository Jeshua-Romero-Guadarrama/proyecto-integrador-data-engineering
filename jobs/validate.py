"""Etapa 3 — Validación: reglas de calidad de datos.

Se ejecuta sobre el DataFrame de entrada (antes de transformar) para "fallar
rápido" si los datos no son confiables. Las reglas se declaran en
config/pipeline.yml, por lo que agregar una validación no requiere tocar código.

Reglas implementadas:
    - columnas requeridas presentes
    - sin valores nulos en columnas clave
    - valores estrictamente positivos en cantidad y precio_unitario
    - cantidad mínima de filas
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from jobs.common import get_logger, load_config

log = get_logger("validate")


class DataQualityError(ValueError):
    """Se lanza cuando una o más reglas de calidad fallan."""


@dataclass
class ValidationReport:
    """Resultado de la validación: lista de checks con su estado."""

    checks: list[dict] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(c["passed"] for c in self.checks)

    def add(self, name: str, passed: bool, detail: str = "") -> None:
        self.checks.append({"check": name, "passed": passed, "detail": detail})

    def as_dict(self) -> dict:
        return {
            "ok": self.ok,
            "total": len(self.checks),
            "passed": sum(c["passed"] for c in self.checks),
            "checks": self.checks,
        }


def validate(df: pd.DataFrame, raise_on_error: bool = True) -> ValidationReport:
    """Aplica las reglas de calidad y devuelve un reporte.

    Args:
        df: DataFrame de entrada.
        raise_on_error: si True, lanza DataQualityError cuando algún check falla.
    """
    cfg = load_config()["validation"]
    report = ValidationReport()

    # 1. Columnas requeridas.
    faltantes = [c for c in cfg["columnas_requeridas"] if c not in df.columns]
    report.add(
        "columnas_requeridas",
        not faltantes,
        f"faltantes={faltantes}" if faltantes else "todas presentes",
    )

    # 2. Cantidad mínima de filas.
    report.add(
        "min_filas",
        len(df) >= cfg["min_filas"],
        f"filas={len(df)} (min={cfg['min_filas']})",
    )

    # 3. Sin nulos en columnas clave.
    for col in cfg["no_nulos"]:
        if col not in df.columns:
            continue
        nulos = int(df[col].isna().sum())
        report.add(f"no_nulos::{col}", nulos == 0, f"nulos={nulos}")

    # 4. Valores estrictamente positivos.
    for col in cfg["positivos"]:
        if col not in df.columns:
            continue
        no_positivos = int((df[col] <= 0).sum())
        report.add(f"positivos::{col}", no_positivos == 0, f"<=0 => {no_positivos}")

    for c in report.checks:
        nivel = log.info if c["passed"] else log.error
        nivel("check %-24s %s (%s)", c["check"], "OK" if c["passed"] else "FALLÓ", c["detail"])

    if raise_on_error and not report.ok:
        fallidos = [c["check"] for c in report.checks if not c["passed"]]
        raise DataQualityError(f"Validaciones fallidas: {fallidos}")

    return report
