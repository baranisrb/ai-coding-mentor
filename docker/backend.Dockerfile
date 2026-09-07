FROM python:3.11-slim

WORKDIR /app

# System deps kept minimal on purpose.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app

# The Gemini API key is passed in at runtime via environment variables
# (docker-compose / `docker run -e`), never baked into the image.
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
