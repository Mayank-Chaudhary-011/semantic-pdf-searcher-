FROM python:3.11-slim

# Install system compiler tools + tesseract-ocr for PDF OCR fallback
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first (for caching)
COPY api/requirements.txt ./api/requirements.txt

# Install python dependencies
RUN pip install --no-cache-dir -r ./api/requirements.txt

# Copy all project files into the container
COPY . .

# Run the FastAPI server using the PORT environment variable provided by Railway
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT}"]
