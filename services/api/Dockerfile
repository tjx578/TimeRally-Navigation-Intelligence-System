FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Pasang dependency
COPY services/api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Salin packages domain dan service API
COPY packages /app/packages
COPY services/api /app/services/api

ENV PYTHONPATH=/app/packages/rally_core/..:/app/packages/geo_engine/..:/app/packages/knowledge_engine/..:/app/packages/data_contracts/..:/app/services/api
WORKDIR /app/services/api

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
