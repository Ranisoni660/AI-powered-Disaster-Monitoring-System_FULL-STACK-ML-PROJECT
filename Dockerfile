# Use Python base with apt
FROM python:3.10-slim

# Prevents prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies needed for building wheels (e.g., blis, murmurhash)
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy models (optional — depends on how you're loading them)
RUN python -m spacy download en_core_web_sm

# Copy project files
COPY . .

# Expose port and set gunicorn as default entry
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000"]

