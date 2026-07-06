{# Test genérico: la columna debe contener sólo valores estrictamente positivos.
   Uso en schema.yml:
       data_tests:
         - positivo
   Falla (devuelve filas) si existe algún valor <= 0. #}
{% test positivo(model, column_name) %}

select {{ column_name }}
from {{ model }}
where {{ column_name }} <= 0

{% endtest %}
