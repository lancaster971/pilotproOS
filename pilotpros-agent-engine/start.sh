#!/bin/bash

# Start job processor worker in background
echo "Starting Agent Engine Job Processor..."
python -m workers.job_processor &
WORKER_PID=$!
echo "Worker started with PID: $WORKER_PID"

# Wait a moment for worker to initialize
sleep 2

# Start main application
echo "Starting Agent Engine API..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload