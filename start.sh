#!/bin/bash

# Terminate all existing tmux sessions to start fresh
tmux kill-server

# Determine the script's directory to use relative paths
SCRIPT_DIR="$(dirname "$(realpath "$BASH_SOURCE")")"
LOG_FILE="$SCRIPT_DIR/startup.log"
TUNNEL_FILE="$SCRIPT_DIR/tunnelled_urls.txt"

# Logging start of the script
echo "Script started" > "$LOG_FILE"

# Delete the file if it already exists
if [ -f "$TUNNEL_FILE" ]; then
    echo "Removing existing tunnelled_urls.txt file." >> "$LOG_FILE"
    rm "$TUNNEL_FILE"
fi

echo "Waiting for network availability..." >> "$LOG_FILE"

# Wait for network to be available
until ping -c1 google.com &>/dev/null; do
    echo "Waiting for network..." >> "$LOG_FILE"
    sleep 1
done

echo "Network is up, proceeding with tmole and Flask app startup." >> "$LOG_FILE"

# Start a new tmux session for tmole
echo "Starting tmole in tmux session." >> "$LOG_FILE"
tmux new-session -d -s tmole "tmole 5005 | tee $TUNNEL_FILE"

# Wait for tmole to initialize and print its URLs
# Wait until the file exists and is non-empty
while [[ ! -s "$TUNNEL_FILE" ]]; do
    echo "Waiting for tmole to output URLs..." >> "$LOG_FILE"
    sleep 1
done

echo "tmole URLs are ready, proceeding with Flask app." >> "$LOG_FILE"

# Start a new tmux session for the Flask app
tmux new-session -d -s flask bash -c "
cd $SCRIPT_DIR &&
source venv/bin/activate &&
python app.py
"

echo "Flask app and tmole are running in tmux sessions." >> "$LOG_FILE"
echo "Use 'tmux attach-session -t tmole' or 'tmux attach-session -t flask' to view sessions." >> "$LOG_FILE"
