"""Genera el dataset de ventas de ejemplo de forma determinista.

Uso:
    python scripts/generate_data.py [--rows N] [--out data/ventas.csv]

El dataset simula ventas diarias de una tienda con las columnas mínimas
requeridas por el proyecto: fecha, producto_id, cantidad, precio_unitario.
La semilla fija garantiza reproducibilidad (mismo output en cada ejecución).
"""
from __future__ import annotations

import argparse
import random
from datetime import date, timedelta
from pathlib import Path

# Catálogo de productos con precio unitario "de lista" (con leve variación diaria).
PRODUCTOS = {
    101: ("Teclado mecanico", 45.00),
    102: ("Mouse inalambrico", 25.50),
    103: ("Monitor 24 pulgadas", 189.90),
    104: ("Auriculares USB", 32.75),
    105: ("Webcam HD", 58.20),
    106: ("Hub USB-C", 22.00),
    107: ("Cable HDMI 2m", 9.99),
    108: ("Soporte para laptop", 34.40),
}

FECHA_INICIO = date(2023, 1, 1)
DIAS = 60  # dos meses de operación


def generar(rows: int, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    filas: list[dict] = []
    producto_ids = list(PRODUCTOS.keys())
    for _ in range(rows):
        dia = rng.randint(0, DIAS - 1)
        fecha = FECHA_INICIO + timedelta(days=dia)
        pid = rng.choice(producto_ids)
        _, precio_base = PRODUCTOS[pid]
        # Pequeña variación de precio (+-5%) para simular promociones/ajustes.
        precio = round(precio_base * rng.uniform(0.95, 1.05), 2)
        cantidad = rng.randint(1, 12)
        filas.append(
            {
                "fecha": fecha.isoformat(),
                "producto_id": pid,
                "cantidad": cantidad,
                "precio_unitario": precio,
            }
        )
    # Orden estable por fecha y producto para facilitar la lectura/diffs.
    filas.sort(key=lambda r: (r["fecha"], r["producto_id"]))
    return filas


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera datos de ventas de ejemplo")
    parser.add_argument("--rows", type=int, default=1000, help="Cantidad de filas")
    parser.add_argument("--out", type=str, default="data/ventas.csv", help="Ruta de salida")
    parser.add_argument("--seed", type=int, default=42, help="Semilla aleatoria")
    args = parser.parse_args()

    filas = generar(args.rows, args.seed)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    import csv

    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["fecha", "producto_id", "cantidad", "precio_unitario"]
        )
        writer.writeheader()
        writer.writerows(filas)

    print(f"[generate_data] {len(filas)} filas escritas en {out}")


if __name__ == "__main__":
    main()
