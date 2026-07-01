# BrokerGuard Field Verify — imagen de produccion (NEXUS-1 / shildoo.com)
FROM python:3.12-slim

# fuentes del sistema para el overlay del geostamp (PIL) y el PDF
RUN apt-get update && apt-get install -y --no-install-recommends \
      fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias primero (capa cacheable)
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY assets ./assets
RUN pip install --no-cache-dir .

# Usuario no-root; cache de tiles y tmp escribibles
RUN useradd -m -u 1001 appuser \
    && mkdir -p /app/cache/osm_tiles /app/tmp \
    && chown -R appuser:appuser /app
USER appuser

ENV OSM_CACHE_DIR=/app/cache/osm_tiles \
    API_HOST=0.0.0.0 \
    API_PORT=8002

EXPOSE 8002

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8002/health', timeout=4)"

CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8002"]
