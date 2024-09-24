#!/bin/bash

# setup.sh - Script to set up the Python virtual environment

ENV_DIR="venv"

# Function to check if Python 3 is installed
function check_python() {
    if ! command -v python3 &> /dev/null; then
        echo "Python 3 is not installed. Please install Python 3 and try again."
        exit 1
    fi
}

# Function to create virtual environment
function create_venv() {
    echo "Creating Python virtual environment..."
    python3 -m venv $ENV_DIR
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment."
        exit 1
    fi
}

# Function to activate virtual environment
function activate_venv() {
    echo "Activating virtual environment..."
    source $ENV_DIR/bin/activate
    if [ $? -ne 0 ]; then
        echo "Failed to activate virtual environment."
        exit 1
    fi
}

# Function to install requirements
function install_requirements() {
    echo "Installing Python packages from requirements.txt..."
    pip install --upgrade pip
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Failed to install Python packages."
        exit 1
    fi
}

# Main script execution
echo "Starting environment setup..."

check_python

# Check if virtual environment already exists
if [ -d "$ENV_DIR" ]; then
    echo "Virtual environment '$ENV_DIR' already exists."
else
    create_venv
fi

activate_venv
install_requirements

echo "Environment setup complete."
echo "To activate the environment in the future, run: source $ENV_DIR/bin/activate"
