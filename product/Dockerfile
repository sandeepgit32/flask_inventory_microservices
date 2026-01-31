FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc curl && rm -rf /var/lib/apt/lists/*

COPY product/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY product/ .
COPY message_queue/ /app/message_queue/

EXPOSE 5000

HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["python", "main.py"]
