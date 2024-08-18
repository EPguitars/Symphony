# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    xvfb \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Update pip to the latest version
RUN python -m pip install --upgrade pip

# Install Python dependencies and Playwright
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir playwright \
    && playwright install-deps \
    && playwright install chromium

# Copy the current directory contents into the container at /app
COPY . .

# Run Playwright with xvfb-run
CMD ["sh", "-c", "pwd && ls -la && xvfb-run -- python core/main.py"]

