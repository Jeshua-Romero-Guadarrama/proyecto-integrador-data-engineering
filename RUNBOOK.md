# 🛠️ Runbook — Pipeline de Ventas

Guía operativa para ejecutar, mantener y resolver problemas del pipeline.

## 1. Puesta en marcha (local)

```bash
pip install -r requirements.txt
python scripts/generate_data.py --rows 1000   # genera data/ventas.csv
python run_pipeline.py                          # corre el pipeline completo
```

Salida esperada: log con las etapas `ingest → validate → transform → load → metrics`
y los archivos en `output/`. Código de salida `0` = éxito.

## 2. Ejecución programada (Airflow)

```bash
docker compose up -d            # levanta Airflow + Prometheus + Grafana
# Airflow UI:  http://localhost:8080  (airflow / airflow)
```

En la UI, activar el DAG `ventas_pipeline` y dispararlo (`Trigger DAG`). El DAG
corre: `generar_datos → ingesta_y_validacion → transformacion_y_carga → dbt_build → reporte`.
Programación por defecto: `@daily`, con `retries=2`.

## 3. Observabilidad

- Métricas locales: `output/metrics/ventas_pipeline.prom` (textfile Prometheus).
- Con Docker: el pipeline empuja al **Pushgateway** (`PUSHGATEWAY_URL`), Prometheus
  las scrapea y Grafana las muestra en el dashboard "Pipeline de Ventas".
- Grafana: http://localhost:3000 (admin / admin) → dashboard aprovisionado.

Métricas clave: `ventas_pipeline_last_success_timestamp`, `_duration_seconds`,
`_rows_in`, `_rows_out`, `_ingreso_total`, `_checks_passed`, `_checks_failed`.

## 4. Verificación de una corrida

1. Revisar el log: todas las líneas `check ...` deben decir `OK`.
2. Revisar `docs/evidence/run_summary.json`: `status = success`, `validation.ok = true`.
3. Confirmar que `output/ingresos_por_producto_fecha.parquet` existe y no está vacío.
4. Regla de sanidad: `rows_out <= rows_in` (la agregación nunca crea filas).

## 5. Troubleshooting

| Síntoma | Causa probable | Solución |
|---------|----------------|----------|
| `FileNotFoundError: data/ventas.csv` | No se generó el dataset | `python scripts/generate_data.py` |
| `SchemaError: columnas requeridas faltantes` | CSV con columnas incorrectas | Revisar el header del CSV vs `config/pipeline.yml` |
| `DataQualityError: Validaciones fallidas` | Datos con nulos o negativos | Inspeccionar la fila; corregir la fuente. El corte es intencional |
| `ModuleNotFoundError: jobs` | `PYTHONPATH` no incluye la raíz | `export PYTHONPATH=$(pwd)` (o `$env:PYTHONPATH` en PowerShell) |
| PySpark: `winutils.exe / HADOOP_HOME unset` | Windows sin Hadoop nativo | El job cae automáticamente al writer pandas; en Linux/Docker usa el nativo |
| dbt: `Runtime Error ... profile` | Falta `--profiles-dir .` | Correr dbt desde `dbt/ventas` con `--profiles-dir .` |

## 6. Mantenimiento

- **Cambiar reglas de calidad**: editar `config/pipeline.yml` (sección `validation`).
- **Cambiar rutas de I/O**: sección `paths` del mismo archivo.
- **Agregar un test**: crear `tests/test_*.py`; CI lo corre automáticamente.
- **Reprocesar**: el pipeline es idempotente — sobrescribe el output en cada corrida.

## 7. Rollback

El output se sobrescribe de forma determinista. Para volver a un estado previo,
basta con re-ejecutar `python run_pipeline.py` con el mismo `data/ventas.csv`
(semilla fija ⇒ mismo resultado). No hay estado mutable externo que revertir.
