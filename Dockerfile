# Use a lightweight Python base image
FROM python:3.11-slim

# Avoid interactive prompts during installs
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies for SQL Server + Postgres
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    apt-transport-https \
    unixodbc \
    unixodbc-dev \
    libgssapi-krb5-2 \
    libpq-dev \
    gcc \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Add Microsoft repository & install ODBC Driver 17 for SQL Server
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64,arm64,armhf signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt ./ 
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory and add a non-root user
RUN mkdir -p /app/logs && \
    adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port (uses Render env var)
EXPOSE ${PORT}

# Start the app with Gunicorn
CMD ["sh", "-c", "gunicorn callback_listener.app:app --bind 0.0.0.0:${PORT} --workers=2 --threads=2 --access-logfile=- --error-logfile=-"]
