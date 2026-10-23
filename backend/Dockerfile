FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for build caching
COPY requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and database migrations
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini

# Expose default API port
EXPOSE 8000

# Environment variables
ENV PYTHONPATH="/app"
ENV HOST=0.0.0.0
ENV PORT=8000

# Run FastAPI via uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
