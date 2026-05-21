FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY services/place-resolver/requirements.txt /tmp/req.txt
RUN pip install --no-cache-dir -r /tmp/req.txt
COPY packages /app/packages
COPY services/place-resolver /app/services/place-resolver
ENV PYTHONPATH=/app/packages/knowledge_engine/..:/app/packages/geo_engine/..:/app/packages/rally_core/..:/app/services/place-resolver
WORKDIR /app/services/place-resolver
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8011
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8011/healthz', timeout=3)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8011"]
