# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code
COPY . .

# Create directories for uploads and temp files
RUN mkdir -p uploads temp_audio

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run main.py when the container launches
CMD ["python", "main.py"]
