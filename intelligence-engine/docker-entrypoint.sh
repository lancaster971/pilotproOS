#!/bin/bash
set -e

echo "🚀 Starting Intelligence Engine..."

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
while ! nc -z ${DB_HOST:-postgres-dev} ${DB_PORT:-5432}; do
    sleep 1
done
echo "✅ PostgreSQL is ready!"

# Wait for Redis
echo "Waiting for Redis..."
while ! nc -z ${REDIS_HOST:-redis-dev} ${REDIS_PORT:-6379}; do
    sleep 1
done
echo "✅ Redis is ready!"

# Initialize database if needed
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running database migrations..."
    python -m app.database.init
fi

# Start services based on environment variable
if [ "$SERVICE_MODE" = "all" ] || [ -z "$SERVICE_MODE" ]; then
    echo "Starting all services..."

    # Start Streamlit UI in background
    streamlit run app/ui/dashboard.py &

    # Start API server
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

elif [ "$SERVICE_MODE" = "api" ]; then
    echo "Starting API only..."
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

elif [ "$SERVICE_MODE" = "ui" ]; then
    echo "Starting UI only..."
    streamlit run app/ui/dashboard.py

else
    echo "Unknown SERVICE_MODE: $SERVICE_MODE"
    exit 1
fi