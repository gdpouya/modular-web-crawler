FROM python:3.11-slim

# System dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir ".[dev,test]"

# Copy application code
COPY src/ ./src/
COPY migrations/ ./migrations/

# Set Python path
ENV PYTHONPATH=/app/src

# Default command
ENTRYPOINT ["crawler"]
