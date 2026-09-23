# MultiPersona AI Voice Agents — Backend Dockerfile
# Python FastAPI + Pipecat voice pipeline
# Lightweight production image for a 2 GB EC2 instance.

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Cache bust arg - ensures fresh build on every commit
ARG CACHEBUST=1

# Copy application code
COPY app/ ./app/
COPY data/ ./data/
COPY scripts/ ./scripts/

# Expose ports (FastAPI with WebSocket endpoint)
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:7860/health || exit 1
# Run the application
CMD ["python", "-m", "app.main"]
