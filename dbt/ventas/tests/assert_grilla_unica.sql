-- Test singular: cada par (fecha, producto_id) debe aparecer una sola vez en
-- la tabla de hechos. El test falla si devuelve alguna fila.

select
    fecha,
    producto_id,
    count(*) as n
from {{ ref('fct_ingresos') }}
group by fecha, producto_id
having count(*) > 1
