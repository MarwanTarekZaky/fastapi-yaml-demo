# Slim base 
FROM python:3.12-slim

# Security/behavior defaults
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UVICORN_WORKERS=2 \
    PORT=8000

# Install system dependencies and create a non-root user
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && rm -rf /var/lib/apt/lists/* \
    && useradd -m appuser

# Set the working directory
WORKDIR /app

# Install Python deps first (leverage layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY app ./app

# Drop root 
USER appuser

EXPOSE 8000
CMD [ "uvicorn", "app.main:app", "--host" , "0.0.0.0", "--port", "8000" ]