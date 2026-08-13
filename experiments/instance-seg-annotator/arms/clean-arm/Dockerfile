FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code.
COPY app ./app
COPY static ./static

# The user's images + annotations are mounted here by docker compose.
ENV DATA_DIR=/data
RUN mkdir -p /data

EXPOSE 8000

# Same entrypoint the tests exercise via uvicorn.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
