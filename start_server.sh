#!/bin/bash
# Start the Scouting Map server
# Usage: ./start_server.sh

cd "$(dirname "$0")"
source ../venv/bin/activate
echo "Starting Scouting Map Server..."
echo "Open http://localhost:5001 in your browser"
echo "Press Ctrl+C to stop"
python server.py
