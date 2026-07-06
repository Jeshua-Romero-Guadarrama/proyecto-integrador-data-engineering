"""Orquestador principal del pipeline de ventas (end-to-end).

Ejecuta, en orden y de forma reproducible:
    ingesta -> validación -> transformación -> carga -> métricas

Uso:
    python run_pipeline.py
    python run_pipeline.py --input data/ventas.csv

Devuelve código de salida 0 si todo el pipeline (incluida la validación de
calidad) fue exitoso; distinto de 0 en caso de error.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from jobs.common import PROJECT_ROOT, get_logger, load_config, resolve


def _rel(path) -> str:
    """Devuelve la ruta relativa a la raíz del proyecto (portable en la evidencia)."""
    try:
        return str(Path(path).resolve().relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)
from jobs.ingest import ingest
from jobs.load import load
from jobs.metrics import emit
from jobs.transform import transform
from jobs.validate import validate

log = get_logger("run_pipeline")


def run(input_path: str | None = None) -> dict:
    """Ejecuta el pipeline completo y devuelve un resumen de la corrida."""
    inicio = time.perf_counter()
    log.info("=== INICIO pipeline de ventas ===")

    # 1. Ingesta
    df = ingest(input_path)
    rows_in = len(df)

    # 2. Validación de calidad (falla rápido si los datos no son confiables)
    report = validate(df, raise_on_error=True)

    # 3. Transformación (reglas de negocio)
    resultado = transform(df)
    rows_out = len(resultado)
    ingreso_total = float(resultado["ingreso_total"].sum())

    # 4. Carga (Parquet + CSV)
    rutas = load(resultado)

    duracion = time.perf_counter() - inicio

    # 5. Observabilidad: métricas Prometheus
    metrics = {
        "ventas_pipeline_last_success_timestamp": time.time(),
        "ventas_pipeline_duration_seconds": round(duracion, 3),
        "ventas_pipeline_rows_in": rows_in,
        "ventas_pipeline_rows_out": rows_out,
        "ventas_pipeline_ingreso_total": round(ingreso_total, 2),
        "ventas_pipeline_checks_passed": sum(c["passed"] for c in report.checks),
        "ventas_pipeline_checks_failed": sum(not c["passed"] for c in report.checks),
    }
    emit(metrics)

    resumen = {
        "status": "success",
        "duration_seconds": round(duracion, 3),
        "rows_in": rows_in,
        "rows_out": rows_out,
        "ingreso_total": round(ingreso_total, 2),
        "validation": report.as_dict(),
        "outputs": {k: _rel(v) for k, v in rutas.items()},
    }

    # Persistir un resumen JSON como evidencia de ejecución.
    cfg = load_config()
    evidence_dir = resolve(cfg["paths"]["evidence_dir"])
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "run_summary.json").write_text(
        json.dumps(resumen, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )

    log.info("Resumen: %s", json.dumps(resumen["outputs"], ensure_ascii=False))
    log.info("=== FIN pipeline en %.3fs (ingreso_total=%.2f) ===", duracion, ingreso_total)
    return resumen


def main() -> int:
    parser = argparse.ArgumentParser(description="Pipeline end-to-end de ventas")
    parser.add_argument("--input", default=None, help="Ruta al CSV de entrada")
    args = parser.parse_args()
    try:
        run(args.input)
        return 0
    except Exception as exc:  # noqa: BLE001
        log.exception("Pipeline FALLÓ: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
