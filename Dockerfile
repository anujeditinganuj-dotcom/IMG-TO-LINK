# ─── Build Stage ───────────────────────────────────────────────
FROM python:3.11-slim

# Working directory
WORKDIR /app

# System deps (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Dependencies pehle copy karo (cache optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Source code copy karo
COPY . .

# Port expose karo (Flask health server)
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Bot start karo
CMD ["python", "main.py"]
