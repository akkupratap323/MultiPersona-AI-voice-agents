# MultiPersona AI Voice Agents — Backend Dockerfile
# Python FastAPI + Pipecat voice pipeline
# Uses CPU-only PyTorch (~800MB vs ~2.5GB with CUDA) to fit 4GB Lightsail RAM

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

# Install CPU-only PyTorch FIRST (before other deps to avoid CUDA version)
# This saves ~1.7GB compared to default PyTorch with CUDA
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Cache bust arg - ensures fresh build on every commit
ARG CACHEBUST=1

# Copy application code
COPY app/ ./app/
COPY data/ ./data/
COPY scripts/ ./scripts/

# Expose ports (FastAPI with WebSocket endpoint)
EXPOSE 7860

# Health check (60s start period for LLM initialization)
HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:7860/health || exit 1
# Note: 60s start-period covers MSP-PODCAST model load time on first boot

# Run the application
CMD ["python", "-m", "app.main"]
