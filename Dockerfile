# Use Python slim image (Debian 12 base for 3.11)
FROM python:3.11-slim

# Environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV ACCEPT_EULA=Y

# Install system dependencies & Microsoft ODBC Driver 17 for SQL Server
RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    apt-transport-https \
    unixodbc \
    unixodbc-dev \
    gcc \
    g++ \
    libssl-dev \
    libffi-dev \
    # Add Microsoft repo for Debian 12
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    # Clean up cache
    && rm -rf /var/lib/apt/lists/*

# Verify driver installation
RUN odbcinst -q -d -n "ODBC Driver 17 for SQL Server" || (echo "❌ ODBC Driver not found!" && exit 1)

# Set working directory
WORKDIR /app

# Copy dependency list first (to leverage Docker caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose application port
EXPOSE 10000


CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]
