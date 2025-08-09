# Use Python slim image
FROM python:3.11-slim

# Environment variables to suppress warnings
ENV DEBIAN_FRONTEND=noninteractive
ENV ACCEPT_EULA=Y

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    apt-transport-https \
    unixodbc \
    unixodbc-dev \
    gcc \
    g++ \
    libssl-dev \
    libffi-dev

# Add Microsoft package signing key and repository for Debian 11
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies + Gunicorn
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Copy the rest of the application
COPY . .

# Expose the application port
EXPOSE 10000

# Run the app with Gunicorn (4 workers, threaded, bound to $PORT for Render)
CMD ["gunicorn", "--workers", "4", "--threads", "2", "--bind", "0.0.0.0:10000", "app:app"]
