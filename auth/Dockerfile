FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY auth/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY auth/ .

# Copy shared message_queue module
COPY message_queue/ /app/message_queue/

# Expose port
EXPOSE 5003

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
    CMD curl -f http://localhost:5003/health || exit 1

# Run application
CMD ["python", "main.py"]
