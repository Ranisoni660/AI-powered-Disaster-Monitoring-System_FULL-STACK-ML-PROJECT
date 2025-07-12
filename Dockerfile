# Use compatible Python version
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# DOWNLOAD the spaCy model to fix the error!
RUN python -m spacy download xx_ent_wiki_sm

# Copy the rest of the application
COPY . .

# Start the app with gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
