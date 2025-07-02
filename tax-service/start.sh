#!/bin/bash
set -e

echo "Starting tax-service initialization..."

# Wait for RabbitMQ to be ready
echo "Waiting for RabbitMQ to be available..."
until timeout 5 bash -c "< /dev/tcp/rabbitmq/5672"; do
  echo "RabbitMQ is unavailable - sleeping"
  sleep 5
done
echo "RabbitMQ is up - continuing"

# Run database migrations
echo "Running database migrations..."
python /app/run_migrations.py

# Start the application
echo "Starting tax-service API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8001
