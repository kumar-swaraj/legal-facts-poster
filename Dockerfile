# syntax=docker/dockerfile:1
FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

# Set working directory
WORKDIR /app

# Install uv from official binary image for fast, reproducible installs
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Environment settings: headless execution, unbuffered logs, pre-installed browsers
ENV PYTHONUNBUFFERED=1 \
    HEADLESS=true \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1 \
    UV_BREAK_SYSTEM_PACKAGES=1

# Copy project definition, licenses, and source code
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src/ ./src/

# Install dependencies and package into system environment using uv
RUN uv pip install --system --break-system-packages --frozen -e .

# Ensure ownership and configure non-root user (pwuser is pre-created by Microsoft Playwright image)
RUN chown -R pwuser:pwuser /app
USER pwuser

# Default persistent volume mount point
VOLUME ["/app/data"]

# Default command runs the scheduled background daemon
CMD ["legal-post", "--headless"]
