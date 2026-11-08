
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

RUN groupadd --system appgroup && \
    useradd --system \
    --gid appgroup \
    --home-dir /app \
    --no-create-home \
    appuser && \
    chown -R appuser:appgroup /app

# Run application as non-root user
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
