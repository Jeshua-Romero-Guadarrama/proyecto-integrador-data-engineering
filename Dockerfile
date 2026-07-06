# Imagen del pipeline de ventas (ingesta + transformación + validación + dbt).
# Incluye Java para poder ejecutar también el job PySpark.
FROM python:3.12-slim

# Java (requerido por PySpark) y utilidades básicas.
RUN apt-get update \
    && apt-get install -y --no-install-recommends default-jre-headless make \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    JAVA_HOME=/usr/lib/jvm/default-java

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Genera datos y ejecuta el pipeline por defecto.
CMD ["sh", "-c", "python scripts/generate_data.py && python run_pipeline.py"]
