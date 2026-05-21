FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY services/tracking-gateway/requirements.txt /tmp/req.txt
RUN pip install --no-cache-dir -r /tmp/req.txt
COPY packages /app/packages
COPY services/tracking-gateway /app/services/tracking-gateway
ENV PYTHONPATH=/app/packages/geo_engine/..:/app/services/tracking-gateway
WORKDIR /app/services/tracking-gateway
EXPOSE 8012
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8012"]
