# Use a lightweight Python base image
FROM python:3.11-slim

# Prevent interactive prompts during package installs
ENV DEBIAN_FRONTEND=noninteractive

# Set a working directory inside the container
WORKDIR /callback_listener/app

# Copy requirements file from the host machine to the working directory in the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the contents of the local 'app' directory into the container's working directory
COPY ./app .

# Default environment variables for Flask
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV FLASK_RUN_HOST=0.0.0.0

# Expose the default port
# (PORT is provided by Render at runtime; default to 5000 locally)
EXPOSE 5000

# Start the Flask application
CMD ["python", "app.py"]
