# Use a lightweight Python base image
FROM python:3.11-slim

# Avoid interactive prompts during installs
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies & SQL Server ODBC driver
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    apt-transport-https \
    unixodbc \
    unixodbc-dev \
    libgssapi-krb5-2 \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Add Microsoft repository & install ODBC Driver 17 using modern keyring approach
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list | tee /etc/apt/sources.list.d/mssql-release.list \
    && sed -i 's|deb |deb [signed-by=/usr/share/keyrings/microsoft-prod.gpg] |' /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose Render port
EXPOSE 10000

# Start app with Gunicorn (Render will override $PORT)
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000", "--workers=4", "--threads=2"]