# ── Stage 1: builder ──────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build tools for heavy packages (LightGBM, CatBoost, XGBoost, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ make libgomp1 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Install dependencies into a separate directory for easy copying
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: runtime ──────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install system runtime libraries (like libgomp1 which is required by LightGBM/XGBoost)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Create exports and artifacts directories, ensuring appropriate permissions
RUN mkdir -p exports artifacts && chmod -R 777 exports artifacts

# Non-root user for security
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# Use python standard library for health checks to keep image clean and secure
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import os, urllib.request; port = os.getenv('PORT', '8000'); urllib.request.urlopen(f'http://localhost:{port}/health')"

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
