# Dockerfile for PDF Parser

# Use official Python image as a base
FROM python:3.12.7-slim-bookworm

# Set working directory for the application
WORKDIR /app

# Create a non-root user and switch to it
# Adding a non-login shell to enhance security by preventing unintended user access
RUN useradd -m -s /usr/sbin/nologin appuser
USER appuser

# Copy Python requirements file first to take advantage of Docker layer caching
COPY requirements.txt ./

# Install required Python packages in a virtual environment
# Creating a virtual environment to prevent conflicts with system-level packages
RUN python -m venv venv && \
    . venv/bin/activate && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
# Copying the main Python script after installing dependencies to reduce rebuild time when code changes
COPY pdf-parser.py ./

# Command to run the script
# Using 'exec' to ensure that Python runs as PID 1, allowing proper signal handling
ENTRYPOINT ["exec", "venv/bin/python", "pdf-parser.py"]