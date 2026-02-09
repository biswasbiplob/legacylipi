# Stage 1: Build frontend
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python application
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-mar \
    tesseract-ocr-hin \
    translate-shell \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster Python package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy Python project files
COPY pyproject.toml uv.lock ./
COPY src/ src/

# Install Python dependencies
RUN uv pip install --system -e ".[all]" || uv pip install --system -e .

# Copy built frontend from stage 1
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

# Copy other necessary files
COPY scripts/ scripts/
COPY README.md ./

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run the API server (serves both API and frontend)
CMD ["uv", "run", "legacylipi", "api", "--host", "0.0.0.0", "--port", "8000"]
