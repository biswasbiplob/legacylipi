# Stage 1: Build frontend
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python application
FROM python:3.12-slim

# Install system dependencies (translate-shell via git.io/trans script)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-mar \
    tesseract-ocr-hin \
    curl \
    gawk \
    && rm -rf /var/lib/apt/lists/* \
    && curl -sL git.io/trans -o /usr/local/bin/trans \
    && chmod +x /usr/local/bin/trans

# Install uv for faster Python package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy all project files needed for install
COPY pyproject.toml uv.lock README.md ./
COPY src/ src/

# Install Python dependencies (non-editable for Docker)
RUN uv pip install --system ".[all]" || uv pip install --system .

# Copy built frontend from stage 1
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

# Copy other necessary files
COPY scripts/ scripts/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run the API server (serves both API and frontend)
CMD ["python", "-m", "legacylipi.api.main"]
