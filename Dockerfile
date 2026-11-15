# FlowETL — Visual Data Integration Platform
# Production Multi-Stage / Lightweight Container Image

FROM python:3.12-slim

# Prevent Python from writing .pyc and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLOWETL_ENV=production \
    FLOWETL_HOST=0.0.0.0 \
    FLOWETL_PORT=8000

WORKDIR /app

# Install minimal OS dependencies for healthcheck & network tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first for caching layers
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Create necessary directories for runtime uploads and data
RUN mkdir -p uploads data output

# Expose Web UI & API port
EXPOSE 8000

# Container healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command: start server
CMD ["python", "run_server.py"]
