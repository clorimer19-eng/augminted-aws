# Base image
FROM python:3.11-slim

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    BLENDER_MAJOR=4.2 \
    BLENDER_VERSION=4.2.0 \
    BLENDER_URL=https://download.blender.org/release/Blender4.2/blender-4.2.0-linux-x64.tar.xz \
    BLENDER_BIN=/usr/local/blender/blender \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    xz-utils \
    libgl1 \
    libxi6 \
    libxrender1 \
    libxxf86vm1 \
    libxfixes3 \
    libxcursor1 \
    libxinerama1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Blender
RUN wget -O blender.tar.xz "$BLENDER_URL" \
    && mkdir /usr/local/blender \
    && tar -xJvf blender.tar.xz -C /usr/local/blender --strip-components=1 \
    && rm blender.tar.xz

# Working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p inputs outputs logs jobs

# Expose port (Cloud Run uses 8080 by default)
ENV PORT=8080
EXPOSE 8080

# Run the API
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
