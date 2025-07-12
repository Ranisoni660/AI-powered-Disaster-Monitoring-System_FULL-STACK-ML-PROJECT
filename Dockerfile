# Use official Python 3.10 image (compatible with spaCy etc.)
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system packages for spaCy models and compilation
RUN apt-get update && apt-get install -y gcc g++ build-essential curl

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy models if needed (optional)
# RUN python -m spacy download en_core_web_sm

# Copy the rest of your code
COPY . .

# Expose port (Render expects this)
EXPOSE 8000

# Run the app using gunicorn (Render will look for this)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
