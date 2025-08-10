#!/bin/bash
set -e

echo "Starting system-monitor-service..."

# Wait for dependencies (Redis, InfluxDB) to be ready
echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 1
done
echo "Redis is ready!"

echo "Waiting for InfluxDB..."
while ! nc -z influxdb 8086; do
  sleep 1
done
echo "InfluxDB is ready!"

# Run Django migrations
echo "Running Django migrations..."
python manage.py migrate

# Start the appropriate service based on command
case "$1" in
  "web")
    echo "Starting Django web server..."
    exec gunicorn server_config.wsgi:application \
      --bind 0.0.0.0:8001 \
      --workers 3 \
      --timeout 60 \
      --access-logfile - \
      --error-logfile -
    ;;
  "worker")
    echo "Starting Celery worker..."
    exec celery -A server_config worker \
      --loglevel=info \
      --concurrency=2
    ;;
  "beat")
    echo "Starting Celery beat scheduler..."
    exec celery -A server_config beat \
      --loglevel=info \
      --scheduler django_celery_beat.schedulers:DatabaseScheduler
    ;;
  *)
    echo "Usage: $0 {web|worker|beat}"
    exit 1
    ;;
esac