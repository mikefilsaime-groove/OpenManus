#!/bin/bash
# Simple launcher script for OpenManus Web UI

# Check if virtual environment exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Virtual environment not found. Please run setup first."
    exit 1
fi

# Check if config.toml exists
if [ ! -f "config/config.toml" ]; then
    echo "Config file not found. Creating from example..."
    cp config/config.example.toml config/config.toml
    echo "Please edit config/config.toml to add your API keys."
    exit 1
fi

# Launch the web interface
python run_web.py
