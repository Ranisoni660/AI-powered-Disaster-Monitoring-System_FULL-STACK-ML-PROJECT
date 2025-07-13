# Use Python
FROM python:3.10

# Set working directory
WORKDIR /app

# Copy your app code
COPY . .

# Install pip dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Install spaCy models
RUN python -m spacy download en_core_web_sm
RUN python -m spacy download xx_ent_wiki_sm

# Expose port
EXPOSE 5000

# Run your app
CMD ["python", "app.py"]
