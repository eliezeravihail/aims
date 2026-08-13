FROM python:3.11-slim

WORKDIR /srv

# Dependencies first for layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Mount points for the input images and output annotations.
RUN mkdir -p /data/images /data/annotations
ENV INPUT_DIR=/data/images \
    ANNOTATIONS_DIR=/data/annotations

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
