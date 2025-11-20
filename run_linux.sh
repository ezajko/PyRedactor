#!/bin/bash

# PyRedactor Launcher for Linux/macOS
# This script launches the application using the virtual environment if available.

# Get the directory where the script is located to ensure we run from project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Check for virtual environment
if [ -f "venv/bin/python" ]; then
    echo "Starting PyRedactor using virtual environment..."
    ./venv/bin/python -m pyredactor.main
elif [ -f "venv/bin/python3" ]; then
    echo "Starting PyRedactor using virtual environment..."
    ./venv/bin/python3 -m pyredactor.main
else
    echo "Virtual environment 'venv' not found."
    echo "Trying global python3..."
    if command -v python3 &> /dev/null; then
        python3 -m pyredactor.main
    else
        echo "Error: python3 not found."
        echo "Please install Python and dependencies as per README.md"
        echo "Press enter to exit"
        read
    fi
fi
