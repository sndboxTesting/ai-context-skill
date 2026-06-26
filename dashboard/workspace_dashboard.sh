#!/bin/bash
# Start the workspace dashboard and open browser
echo "Starting workspace dashboard server..."

# Check if port 7777 is in use
if lsof -Pi :7777 -sTCP:LISTEN -t >/dev/null ; then
    echo "Port 7777 is already in use. Opening browser..."
    open http://localhost:7777
else
    # Open the browser in 1 second
    (sleep 1 && open http://localhost:7777) &
    # Run uvicorn server
    cd "/Users/MAC/SuneelWorkSpace"
    exec uvicorn dashboard.server:app --host 127.0.0.1 --port 7777 --log-level warning
fi
