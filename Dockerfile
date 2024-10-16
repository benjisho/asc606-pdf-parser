# Dockerfile for PDF Parser

# Use official Python image as a base
FROM python:3.12.7-slim-bookworm

# Set working directory for the application
WORKDIR /app

# Copy Python requirements file first to take advantage of Docker layer caching
COPY requirements.txt ./

# Install required Python packages in a virtual environment
# Creating a virtual environment to prevent conflicts with system-level packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
# Copying the main Python script after installing dependencies to reduce rebuild time when code changes
COPY pdf-parser ./

# Command to run the script
# Using 'python' to run the script
ENTRYPOINT ["python3", "asc606-pdf-parser"]
