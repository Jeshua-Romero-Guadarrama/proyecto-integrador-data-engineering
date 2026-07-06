"""Arma un Markdown de evidencia con el esquema y una muestra del output final."""
from __future__ import annotations

from pathlib import Path

import pyarrow.parquet as pq

RAIZ = Path(__file__).resolve().parent.parent
PARQUET = RAIZ / "output" / "ingresos_por_producto_fecha.parquet"
SALIDA = RAIZ / "docs" / "evidence" / "05_output_preview.md"


def main() -> None:
    """Lee el Parquet final y arma el Markdown de evidencia con esquema y muestra."""
    tabla = pq.read_table(PARQUET)
    datos = tabla.to_pandas()

    lineas: list[str] = []
    lineas.append("# Evidencia — Output final (Parquet)\n")
    lineas.append(f"- Archivo: `{PARQUET.relative_to(RAIZ)}`")
    lineas.append(f"- Filas: **{len(datos)}**")
    lineas.append(f"- Columnas: {list(datos.columns)}\n")

    lineas.append("## Esquema Parquet\n")
    lineas.append("```")
    lineas.append(str(tabla.schema))
    lineas.append("```\n")

    lineas.append("## Primeras 15 filas\n")
    lineas.append("```")
    lineas.append(datos.head(15).to_string(index=False))
    lineas.append("```\n")

    lineas.append("## Métricas agregadas de negocio\n")
    lineas.append("```")
    lineas.append(f"Ingreso total global : {datos['ingreso_total'].sum():,.2f}")
    lineas.append(f"Unidades vendidas    : {int(datos['unidades_vendidas'].sum())}")
    lineas.append(f"Productos distintos  : {datos['producto_id'].nunique()}")
    lineas.append(f"Rango de fechas      : {datos['fecha'].min()} a {datos['fecha'].max()}")
    lineas.append("```")

    SALIDA.write_text("\n".join(lineas), encoding="utf-8")
    print(f"Evidencia escrita en {SALIDA}")


if __name__ == "__main__":
    main()
