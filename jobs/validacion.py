"""Etapa 3 — Validación: reglas de calidad antes de transformar.

La idea es cortar temprano ("fail fast"): si los datos vienen mal, mejor
enterarme acá que generar un output que parezca correcto pero no lo sea.
Las reglas viven en config/pipeline.yml, así que para sumar una validación
alcanza con tocar el YAML, sin cambiar este código.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from jobs.comunes import cargar_config, obtener_logger

log = obtener_logger("validacion")


class ErrorCalidadDatos(ValueError):
    """La lanzo cuando falla al menos una regla de calidad."""


@dataclass
class ReporteValidacion:
    """Junta el resultado de cada chequeo para poder revisarlo o loguearlo."""

    chequeos: list[dict] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(c["ok"] for c in self.chequeos)

    def agregar(self, nombre: str, paso: bool, detalle: str = "") -> None:
        self.chequeos.append({"chequeo": nombre, "ok": paso, "detalle": detalle})

    def como_dict(self) -> dict:
        return {
            "ok": self.ok,
            "total": len(self.chequeos),
            "aprobados": sum(c["ok"] for c in self.chequeos),
            "chequeos": self.chequeos,
        }


def validar(datos: pd.DataFrame, lanzar_error: bool = True) -> ReporteValidacion:
    """Corre todas las reglas de calidad y arma el reporte.

    Si lanzar_error es True (lo normal en producción), tira ErrorCalidadDatos
    cuando algo falla. Lo pongo en False en los tests para inspeccionar el
    reporte sin que corte la ejecución.
    """
    reglas = cargar_config()["validation"]
    reporte = ReporteValidacion()

    # 1. Que estén todas las columnas obligatorias.
    faltantes = [c for c in reglas["columnas_requeridas"] if c not in datos.columns]
    reporte.agregar(
        "columnas_requeridas",
        not faltantes,
        f"faltantes={faltantes}" if faltantes else "todas presentes",
    )

    # 2. Que haya al menos la cantidad mínima de filas.
    reporte.agregar(
        "min_filas",
        len(datos) >= reglas["min_filas"],
        f"filas={len(datos)} (min={reglas['min_filas']})",
    )

    # 3. Que no haya nulos en las columnas clave.
    for columna in reglas["no_nulos"]:
        if columna not in datos.columns:
            continue
        nulos = int(datos[columna].isna().sum())
        reporte.agregar(f"no_nulos::{columna}", nulos == 0, f"nulos={nulos}")

    # 4. Que cantidad y precio sean estrictamente positivos.
    for columna in reglas["positivos"]:
        if columna not in datos.columns:
            continue
        no_positivos = int((datos[columna] <= 0).sum())
        reporte.agregar(f"positivos::{columna}", no_positivos == 0, f"<=0 => {no_positivos}")

    # Dejo traza de cada chequeo: info si pasó, error si no.
    for c in reporte.chequeos:
        registrar = log.info if c["ok"] else log.error
        registrar("chequeo %-24s %s (%s)", c["chequeo"], "OK" if c["ok"] else "FALLÓ", c["detalle"])

    if lanzar_error and not reporte.ok:
        fallidos = [c["chequeo"] for c in reporte.chequeos if not c["ok"]]
        raise ErrorCalidadDatos(f"Validaciones fallidas: {fallidos}")

    return reporte
