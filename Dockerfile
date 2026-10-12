# syntax=docker/dockerfile:1
FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

# Set working directory
WORKDIR /app

# Install uv from official binary image for fast, reproducible installs
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Environment settings: headless execution, unbuffered logs, pre-installed browsers
ENV PYTHONUNBUFFERED=1 \
    HEADLESS=true \
    PYTHONDONTWRITEBYTECODE=1

# Copy dependency specifications first for Docker layer caching
COPY pyproject.toml uv.lock ./

# Install project dependencies into system environment using uv
RUN uv pip install --system --frozen -e .

# Copy source code and documentation
COPY src/ ./src/
COPY README.md LICENSE ./

# Re-install package in editable mode to register CLI console scripts
RUN uv pip install --system --no-deps -e .

# Default persistent volume mount point
VOLUME ["/app/data"]

# Default command runs the scheduled background daemon
CMD ["legal-post", "--headless"]
