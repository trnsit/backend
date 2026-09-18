FROM python:3.11-slim

WORKDIR /app

# Install system build dependencies (e.g., tree-sitter, greenlet, psycopg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY . .

# Set Python environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Default command (overridden per service in docker-compose.yml)
CMD ["uvicorn", "services.accounts.main:app", "--host", "0.0.0.0", "--port", "8001"]
