# Use a lightweight Python 3.11 base image to keep the container small
FROM python:3.11-slim

# Prevent interactive prompts during package installation (like tzdata asking for input)
ENV DEBIAN_FRONTEND=noninteractive

# Set the working directory inside the container
# All subsequent commands will be executed relative to this directory
WORKDIR /callback_listener

# Copy the requirements.txt file from your local machine into the container's working directory
COPY requirements.txt .

# Install the Python dependencies listed in requirements.txt
# --no-cache-dir avoids caching wheels to keep the image size smaller
RUN pip install --no-cache-dir -r requirements.txt

# Copy all contents of your local 'callback_listener' folder directly into the working directory inside the container
# This ensures app.py and all modules are placed in /callback_listener inside the container
COPY ./callback_listener .

# Set environment variables for Flask to configure the app
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV FLASK_RUN_HOST=0.0.0.0      

# Expose port 5000, which Flask uses by default
# This lets Docker and hosting services know which port your app listens on
EXPOSE 5000

# Run the Flask app when the container starts
# 'python app.py' starts your Flask application
CMD ["python", "app.py"]
