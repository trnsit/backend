# Base Image: The official lightweight Python 3.11 on Debian Linux
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install system C-compilers needed for tree-sitter, greenlet, psycopg
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Leverage Docker layer caching for Python packages
# Copy ONLY requirements.txt first so Docker caches installed packages.
COPY requirements.txt .

# Code edits later will NOT trigger a slow re-install!
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend application code into /app
COPY . .

# Set Python environment variables
# - PYTHONPATH: Allows importing 'app.*' and 'services.*' seamlessly
ENV PYTHONPATH=/app

# - PYTHONUNBUFFERED: Flushes logs immediately to terminal without delay
ENV PYTHONUNBUFFERED=1

# Default fallback command (overridden per service in docker-compose.yml)
CMD ["uvicorn", "services.accounts.main:app", "--host", "0.0.0.0", "--port", "8001"]
