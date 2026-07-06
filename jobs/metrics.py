"""Instrumentación de observabilidad (Prometheus).

Escribe métricas del pipeline en dos destinos complementarios:
    1. Un archivo textfile (.prom) compatible con el node_exporter textfile
       collector — funciona siempre, sin dependencias de red.
    2. Un Pushgateway, sólo si la variable de entorno PUSHGATEWAY_URL existe
       (útil dentro de docker-compose con Prometheus + Grafana).

Métricas expuestas:
    ventas_pipeline_last_success_timestamp
    ventas_pipeline_duration_seconds
    ventas_pipeline_rows_in
    ventas_pipeline_rows_out
    ventas_pipeline_ingreso_total
    ventas_pipeline_checks_passed / _failed
"""
from __future__ import annotations

import os
from pathlib import Path

from jobs.common import get_logger, load_config, resolve

log = get_logger("metrics")


def _render_prom(metrics: dict[str, float], job: str) -> str:
    lines: list[str] = []
    for name, value in metrics.items():
        lines.append(f"# TYPE {name} gauge")
        lines.append(f'{name}{{job="{job}"}} {value}')
    return "\n".join(lines) + "\n"


def emit(metrics: dict[str, float]) -> Path:
    """Escribe las métricas a textfile y (si aplica) las empuja al Pushgateway."""
    cfg = load_config()
    job = cfg["observability"]["job_name"]
    metrics_dir = resolve(cfg["paths"]["metrics_dir"])
    metrics_dir.mkdir(parents=True, exist_ok=True)
    out = metrics_dir / f"{job}.prom"
    out.write_text(_render_prom(metrics, job), encoding="utf-8")
    log.info("Métricas escritas en textfile: %s", out)

    pushgateway = os.getenv(cfg["observability"]["pushgateway_url_env"])
    if pushgateway:
        try:
            from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

            registry = CollectorRegistry()
            for name, value in metrics.items():
                g = Gauge(name, name, registry=registry)
                g.set(value)
            push_to_gateway(pushgateway, job=job, registry=registry)
            log.info("Métricas empujadas a Pushgateway: %s", pushgateway)
        except Exception as exc:  # noqa: BLE001 — la observabilidad no debe romper el pipeline
            log.warning("No se pudo empujar a Pushgateway (%s): %s", pushgateway, exc)

    return out
