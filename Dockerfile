# Use the official Python image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpoppler-cpp-dev \
    poppler-utils \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source code
COPY . .

# Copy .env (only if you want to bake it in — not recommended for production)
# COPY .env .env

# Expose port (Cloud Run uses 8080 by default)
EXPOSE 8080

# Start app using Uvicorn (Cloud Run looks for 'app' in main module)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]