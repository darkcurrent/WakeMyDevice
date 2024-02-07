#!/bin/bash

# Create a Python virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install Python dependencies from requirements.txt
pip install -r requirements.txt

# Install tmux if not already installed (Debian/Ubuntu specific, adjust for other systems)
if ! command -v tmux &> /dev/null; then
    echo "tmux could not be found, installing..."
    sudo apt-get update && sudo apt-get install tmux
fi

echo "Installation completed successfully. Please ensure Node.js, npm, and TunnelMole are installed as described in the README."
