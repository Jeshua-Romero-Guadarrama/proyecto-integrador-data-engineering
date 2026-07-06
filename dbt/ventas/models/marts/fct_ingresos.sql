-- Tabla de hechos: ingreso total agregado por (fecha, producto_id).
-- Equivalente en SQL al output de jobs/transform.py (misma regla de negocio),
-- lo que permite validar cruzadamente ambas implementaciones.

with base as (
    select * from {{ ref('stg_ventas') }}
)

select
    fecha,
    producto_id,
    sum(cantidad)                as unidades_vendidas,
    round(sum(ingreso_linea), 2) as ingreso_total
from base
group by fecha, producto_id
order by fecha, producto_id
