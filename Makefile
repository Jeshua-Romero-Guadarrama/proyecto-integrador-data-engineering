# Makefile — atajos operativos del pipeline.
# En Windows podés usar `make` (via Git Bash / choco) o correr los comandos python directamente.

.PHONY: help install data run test lint spark dbt clean docker-up docker-down

help:
	@echo "Targets disponibles:"
	@echo "  make install     Instala dependencias (pip)"
	@echo "  make data        Genera el dataset de ejemplo"
	@echo "  make run         Ejecuta el pipeline end-to-end"
	@echo "  make test        Corre la suite de tests (pytest)"
	@echo "  make spark       Ejecuta el job PySpark"
	@echo "  make dbt         Corre los modelos y tests de dbt"
	@echo "  make docker-up   Levanta Airflow + Prometheus + Grafana"
	@echo "  make clean       Limpia outputs y cachés"

install:
	python -m pip install -r requirements.txt

data:
	python scripts/generate_data.py --rows 1000

run:
	python run_pipeline.py

test:
	pytest

lint:
	ruff check .

spark:
	python jobs/spark_job.py --input data/ventas.csv --output output/spark_parquet

dbt:
	cd dbt/ventas && dbt build --profiles-dir .

docker-up:
	docker compose up -d

docker-down:
	docker compose down -v

clean:
	rm -rf output/*.parquet output/*.csv output/metrics output/spark_parquet
	rm -rf .pytest_cache dbt/ventas/target dbt/ventas/logs *.duckdb
