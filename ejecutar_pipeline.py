"""Orquestador del pipeline de ventas de punta a punta.

Corre las etapas en orden y de forma reproducible:
    ingesta -> validación -> transformación -> carga -> métricas

Uso:
    python ejecutar_pipeline.py
    python ejecutar_pipeline.py --entrada data/ventas.csv

Devuelve 0 si todo salió bien (incluida la validación de calidad) y distinto
de 0 si algo falló, para que sirva en un cron o en CI.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from jobs.carga import guardar
from jobs.comunes import RAIZ_PROYECTO, cargar_config, obtener_logger, resolver_ruta
from jobs.ingesta import ingerir
from jobs.metricas import emitir
from jobs.transformacion import transformar
from jobs.validacion import validar

log = obtener_logger("ejecutar_pipeline")


def _relativa(ruta) -> str:
    """Pasa una ruta absoluta a relativa desde la raíz, para que la evidencia sea portable."""
    try:
        return str(Path(ruta).resolve().relative_to(RAIZ_PROYECTO)).replace("\\", "/")
    except ValueError:
        return str(ruta)


def ejecutar(ruta_entrada: str | None = None) -> dict:
    """Corre el pipeline completo y devuelve un resumen de lo que pasó."""
    inicio = time.perf_counter()
    log.info("=== INICIO pipeline de ventas ===")

    # 1. Ingesta
    datos = ingerir(ruta_entrada)
    filas_entrada = len(datos)

    # 2. Validación de calidad (corta acá si los datos no son confiables)
    reporte = validar(datos, lanzar_error=True)

    # 3. Transformación (reglas de negocio)
    resultado = transformar(datos)
    filas_salida = len(resultado)
    ingreso_total = float(resultado["ingreso_total"].sum())

    # 4. Carga (Parquet + CSV)
    rutas = guardar(resultado)

    duracion = time.perf_counter() - inicio

    # 5. Observabilidad: métricas de la corrida
    metricas = {
        "ventas_pipeline_ultimo_exito_timestamp": time.time(),
        "ventas_pipeline_duracion_segundos": round(duracion, 3),
        "ventas_pipeline_filas_entrada": filas_entrada,
        "ventas_pipeline_filas_salida": filas_salida,
        "ventas_pipeline_ingreso_total": round(ingreso_total, 2),
        "ventas_pipeline_chequeos_ok": sum(c["ok"] for c in reporte.chequeos),
        "ventas_pipeline_chequeos_fallidos": sum(not c["ok"] for c in reporte.chequeos),
    }
    emitir(metricas)

    resumen = {
        "estado": "exito",
        "duracion_segundos": round(duracion, 3),
        "filas_entrada": filas_entrada,
        "filas_salida": filas_salida,
        "ingreso_total": round(ingreso_total, 2),
        "validacion": reporte.como_dict(),
        "salidas": {clave: _relativa(valor) for clave, valor in rutas.items()},
    }

    # Guardo el resumen como evidencia de la corrida.
    config = cargar_config()
    carpeta_evidencia = resolver_ruta(config["paths"]["evidence_dir"])
    carpeta_evidencia.mkdir(parents=True, exist_ok=True)
    (carpeta_evidencia / "run_summary.json").write_text(
        json.dumps(resumen, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )

    log.info("Salidas: %s", json.dumps(resumen["salidas"], ensure_ascii=False))
    log.info("=== FIN pipeline en %.3fs (ingreso_total=%.2f) ===", duracion, ingreso_total)
    return resumen


def main() -> int:
    """Punto de entrada de la CLI: parsea argumentos y devuelve el código de salida."""
    parser = argparse.ArgumentParser(description="Pipeline de ventas de punta a punta")
    parser.add_argument("--entrada", default=None, help="Ruta al CSV de entrada")
    args = parser.parse_args()
    try:
        ejecutar(args.entrada)
        return 0
    except Exception as error:  # noqa: BLE001
        log.exception("El pipeline FALLÓ: %s", error)
        return 1


if __name__ == "__main__":
    sys.exit(main())
