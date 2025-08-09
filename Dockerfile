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
  && rm -rf /var/lib/apt/lists/*

# Add Microsoft repository & install ODBC Driver 17
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
  && curl https://packages.microsoft.com/config/debian/12/prod.list \
    > /etc/apt/sources.list.d/mssql-release.list \
  && apt-get update \
  && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
  && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy in app source
COPY . .

# Install all Python dependencies, pinning Werkzeug to latest 3.1.3
RUN pip install --no-cache-dir \
    blinker==1.9.0 \
    click==8.2.1 \
    colorama==0.4.6 \
    Flask==2.3.3 \
    itsdangerous==2.2.0 \
    Jinja2==3.1.6 \
    MarkupSafe==3.0.2 \
    pyodbc==5.2.0 \
    python-dotenv==1.1.1 \
    Werkzeug==3.1.3 \
    gunicorn

# Expose app port
EXPOSE 5000

# Launch app with Gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--workers=4", "--threads=2"]
