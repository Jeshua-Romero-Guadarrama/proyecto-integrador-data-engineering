"""Genera un archivo Markdown de evidencia con el esquema y muestra del output."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parent.parent
PARQUET = ROOT / "output" / "ingresos_por_producto_fecha.parquet"
OUT = ROOT / "docs" / "evidence" / "05_output_preview.md"


def main() -> None:
    table = pq.read_table(PARQUET)
    df = table.to_pandas()

    lines: list[str] = []
    lines.append("# Evidencia — Output final (Parquet)\n")
    lines.append(f"- Archivo: `{PARQUET.relative_to(ROOT)}`")
    lines.append(f"- Filas: **{len(df)}**")
    lines.append(f"- Columnas: {list(df.columns)}\n")

    lines.append("## Esquema Parquet\n")
    lines.append("```")
    lines.append(str(table.schema))
    lines.append("```\n")

    lines.append("## Primeras 15 filas\n")
    lines.append("```")
    lines.append(df.head(15).to_string(index=False))
    lines.append("```\n")

    lines.append("## Métricas agregadas de negocio\n")
    lines.append("```")
    lines.append(f"Ingreso total global : {df['ingreso_total'].sum():,.2f}")
    lines.append(f"Unidades vendidas    : {int(df['unidades_vendidas'].sum())}")
    lines.append(f"Productos distintos  : {df['producto_id'].nunique()}")
    lines.append(f"Rango de fechas      : {df['fecha'].min()} a {df['fecha'].max()}")
    lines.append("```")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Evidencia escrita en {OUT}")


if __name__ == "__main__":
    main()
