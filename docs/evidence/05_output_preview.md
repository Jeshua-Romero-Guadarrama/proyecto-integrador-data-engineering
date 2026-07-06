# Evidencia — Output final (Parquet)

- Archivo: `output\ingresos_por_producto_fecha.parquet`
- Filas: **426**
- Columnas: ['fecha', 'producto_id', 'unidades_vendidas', 'ingreso_total']

## Esquema Parquet

```
fecha: date32[day]
producto_id: int64
unidades_vendidas: int64
ingreso_total: double
-- schema metadata --
pandas: '{"index_columns": [], "column_indexes": [], "columns": [{"name":' + 577
```

## Primeras 15 filas

```
     fecha  producto_id  unidades_vendidas  ingreso_total
2023-01-01          101                  1          46.61
2023-01-01          103                 23        4419.93
2023-01-01          104                  8         261.24
2023-01-01          105                 14         823.88
2023-01-01          107                 30         294.28
2023-01-01          108                 10          348.2
2023-01-02          101                  7          319.8
2023-01-02          102                 24         610.39
2023-01-02          104                 23         758.27
2023-01-02          105                 18         1043.7
2023-01-02          106                 15         326.65
2023-01-02          107                 14         141.78
2023-01-02          108                 14         470.48
2023-01-03          101                 22         991.54
2023-01-03          102                  8         206.56
```

## Métricas agregadas de negocio

```
Ingreso total global : 342,413.79
Unidades vendidas    : 6784
Productos distintos  : 8
Rango de fechas      : 2023-01-01 a 2023-03-01
```