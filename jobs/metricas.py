"""Observabilidad: publico las métricas de cada corrida para Prometheus.

Escribo en dos lados según lo que haya disponible:
    1. Un archivo .prom (textfile) que siempre funciona, sin depender de la red.
    2. Un Pushgateway, pero solo si está seteada la variable PUSHGATEWAY_URL
       (es el caso cuando levanto el stack con docker-compose).

Si el push falla no quiero que se caiga el pipeline por eso: la métrica es
importante, pero secundaria frente a generar el output.
"""
from __future__ import annotations

import os
from pathlib import Path

from jobs.comunes import cargar_config, obtener_logger, resolver_ruta

log = obtener_logger("metricas")


def _armar_texto_prom(metricas: dict[str, float], job: str) -> str:
    """Arma el texto en el formato que espera Prometheus (una gauge por métrica)."""
    lineas: list[str] = []
    for nombre, valor in metricas.items():
        lineas.append(f"# TYPE {nombre} gauge")
        lineas.append(f'{nombre}{{job="{job}"}} {valor}')
    return "\n".join(lineas) + "\n"


def emitir(metricas: dict[str, float]) -> Path:
    """Guarda las métricas en el textfile y, si se puede, las manda al Pushgateway."""
    config = cargar_config()
    job = config["observability"]["job_name"]
    carpeta_metricas = resolver_ruta(config["paths"]["metrics_dir"])
    carpeta_metricas.mkdir(parents=True, exist_ok=True)
    archivo = carpeta_metricas / f"{job}.prom"
    archivo.write_text(_armar_texto_prom(metricas, job), encoding="utf-8")
    log.info("Métricas guardadas en textfile: %s", archivo)

    pushgateway = os.getenv(config["observability"]["pushgateway_url_env"])
    if pushgateway:
        try:
            from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

            registro = CollectorRegistry()
            for nombre, valor in metricas.items():
                gauge = Gauge(nombre, nombre, registry=registro)
                gauge.set(valor)
            push_to_gateway(pushgateway, job=job, registry=registro)
            log.info("Métricas enviadas al Pushgateway: %s", pushgateway)
        except Exception as error:  # noqa: BLE001 — la observabilidad no debe romper la corrida
            log.warning("No pude enviar al Pushgateway (%s): %s", pushgateway, error)

    return archivo
