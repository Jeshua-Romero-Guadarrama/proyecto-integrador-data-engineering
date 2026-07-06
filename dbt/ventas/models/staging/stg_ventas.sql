-- Modelo de staging: lee el CSV crudo de ventas y normaliza tipos.
-- DuckDB puede leer CSV directamente con read_csv_auto, sin cargas previas.

with fuente as (
    select *
    from read_csv_auto('{{ var("ruta_ventas") }}', header = true)
)

select
    cast(fecha as date)              as fecha,
    cast(producto_id as integer)     as producto_id,
    cast(cantidad as integer)        as cantidad,
    cast(precio_unitario as double)  as precio_unitario,
    -- Regla de negocio: ingreso por línea de venta.
    round(cast(cantidad as double) * cast(precio_unitario as double), 2) as ingreso_linea
from fuente
