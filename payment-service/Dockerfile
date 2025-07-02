FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy migration script
COPY run_migrations.py /app/

# Make migration script executable
RUN chmod +x /app/run_migrations.py

# Copy start script
COPY start.sh /app/
RUN chmod +x /app/start.sh

# Expose port
EXPOSE 8004

# Command to run migrations and start the application
CMD ["/app/start.sh"]
