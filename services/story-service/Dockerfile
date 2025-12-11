# Story Service Dockerfile
# Per T034 [US1]: Python 3.11-slim with FastAPI
# Multi-stage build for smaller image size

# Build stage
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY services/story-service/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
#COPY --from=builder /root/.local /root/.local (Gemini)
COPY --from=builder /root/.local /home/appuser/.local
# Make sure scripts in .local are usable
#ENV PATH=/root/.local/bin:$PATH (Gemini)
ENV PATH=/home/appuser/.local/bin:$PATH


# Copy shared libraries (from project root context)
COPY shared/lib-logging /app/shared/lib_logging
COPY shared/lib-tracing /app/shared/lib_tracing
COPY shared/lib-config /app/shared/lib_config

# Add shared libraries to Python path
ENV PYTHONPATH="/app/shared:${PYTHONPATH}"

# Copy application code (includes logging_config.json)
COPY services/story-service/src/ ./src/
COPY services/story-service/start.sh ./
RUN chmod +x start.sh


# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app &&\
    chown -R appuser:appuser /home/appuser/.local

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application via startup script
CMD ["./start.sh"]
