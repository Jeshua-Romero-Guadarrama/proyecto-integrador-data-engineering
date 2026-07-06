"""Genera el CSV de ventas de ejemplo, siempre igual (determinista).

Uso:
    python scripts/generar_datos.py [--filas N] [--salida data/ventas.csv]

Simula ventas diarias de una tienda con las columnas mínimas que pide el
proyecto: fecha, producto_id, cantidad y precio_unitario. Fijo la semilla para
que cada vez que lo corra salga exactamente el mismo dataset.
"""
from __future__ import annotations

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

# Catálogo de productos con su precio "de lista" (después le meto una variación
# chica por día para simular promos o ajustes de precio).
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


def generar(filas: int, semilla: int = 42) -> list[dict]:
    """Arma la lista de ventas. Uso un Random con semilla propia para no
    depender del estado global de random y mantener la reproducibilidad."""
    azar = random.Random(semilla)
    registros: list[dict] = []
    ids_producto = list(PRODUCTOS.keys())
    for _ in range(filas):
        dia = azar.randint(0, DIAS - 1)
        fecha = FECHA_INICIO + timedelta(days=dia)
        pid = azar.choice(ids_producto)
        _, precio_base = PRODUCTOS[pid]
        # Variación de +-5% sobre el precio de lista.
        precio = round(precio_base * azar.uniform(0.95, 1.05), 2)
        cantidad = azar.randint(1, 12)
        registros.append(
            {
                "fecha": fecha.isoformat(),
                "producto_id": pid,
                "cantidad": cantidad,
                "precio_unitario": precio,
            }
        )
    # Ordeno por fecha y producto para que el archivo quede prolijo y los diffs
    # entre corridas sean mínimos.
    registros.sort(key=lambda r: (r["fecha"], r["producto_id"]))
    return registros


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera datos de ventas de ejemplo")
    parser.add_argument("--filas", type=int, default=1000, help="Cantidad de filas")
    parser.add_argument("--salida", type=str, default="data/ventas.csv", help="Ruta de salida")
    parser.add_argument("--semilla", type=int, default=42, help="Semilla del azar")
    args = parser.parse_args()

    registros = generar(args.filas, args.semilla)

    salida = Path(args.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    with salida.open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(
            archivo, fieldnames=["fecha", "producto_id", "cantidad", "precio_unitario"]
        )
        escritor.writeheader()
        escritor.writerows(registros)

    print(f"[generar_datos] {len(registros)} filas escritas en {salida}")


if __name__ == "__main__":
    main()
