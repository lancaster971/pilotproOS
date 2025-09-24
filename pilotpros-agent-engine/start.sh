#!/bin/bash

# Start worker in background
echo "Starting Agent Engine Worker..."
python worker.py &

# Start main application
echo "Starting Agent Engine API..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload