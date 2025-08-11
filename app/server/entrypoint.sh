#!/bin/bash
set -e

echo "Starting system-monitor-service..."

# Wait for dependencies (Redis, InfluxDB) to be ready
echo "Waiting for Redis..."
while ! nc -z localhost 6379; do
  sleep 1
done
echo "Redis is ready!"

echo "Waiting for InfluxDB..."
while ! nc -z localhost 8086; do
  sleep 1
done
echo "InfluxDB is ready!"

# Validate agent connection
echo "Checking agent connection..."
AGENT_HOST=${AGENT_HOST:-127.0.0.1}
AGENT_PORT=${AGENT_PORT:-8000}

echo "Attempting to connect to agent at ${AGENT_HOST}:${AGENT_PORT}"
if curl -f -s "http://${AGENT_HOST}:${AGENT_PORT}/health" > /dev/null; then
    echo "✓ Agent connection successful"
else
    echo "⚠ Warning: Cannot connect to agent at ${AGENT_HOST}:${AGENT_PORT}"
    echo "Make sure the agent is running with:"
    echo "  python -m app.agent.main --server"
    echo ""
    echo "The server will still start, but polling will fail until agent is available."
fi

# Run Django migrations
echo "Running Django migrations..."
python manage.py migrate

# Start the appropriate service based on command
case "$1" in
  "web")
    echo "Starting Django web server..."
    echo "Agent URL: http://${AGENT_HOST}:${AGENT_PORT}/graphql"
    echo "Server will be accessible on port 8001"
    exec gunicorn server_config.wsgi:application \
      --bind 0.0.0.0:8001 \
      --workers 3 \
      --timeout 60 \
      --access-logfile - \
      --error-logfile -
    ;;
  "worker")
    echo "Starting Celery worker..."
    echo "Agent URL: http://${AGENT_HOST}:${AGENT_PORT}/graphql"
    exec celery -A server_config worker \
      --loglevel=info \
      --concurrency=2
    ;;
  "beat")
    echo "Starting Celery beat scheduler..."
    echo "Agent URL: http://${AGENT_HOST}:${AGENT_PORT}/graphql"
    exec celery -A server_config beat \
      --loglevel=info \
      --scheduler django_celery_beat.schedulers:DatabaseScheduler
    ;;
  *)
    echo "Usage: $0 {web|worker|beat}"
    exit 1
    ;;
esac