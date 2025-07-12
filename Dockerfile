# Use compatible Python version
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy models
RUN python -m spacy download xx_ent_wiki_sm
RUN python -m spacy download en_core_web_sm


# Copy the rest of the application
COPY . .

# Start the app with gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
