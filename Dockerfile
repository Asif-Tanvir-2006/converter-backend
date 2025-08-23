# Use slim Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system deps for ffmpeg and Pillow
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY app.py .
# (Optional) copy any static files if you have them

# Expose port
EXPOSE 5000

# Run the app
CMD ["python", "app.py"]

