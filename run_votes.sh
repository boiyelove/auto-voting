#!/bin/bash

echo "Starting voting automation script..."

# Check if virtual environment exists
if [ ! -d "selenium_env" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv selenium_env
    
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment. Please check your Python installation."
        exit 1
    fi
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source selenium_env/bin/activate

# Check if required packages are installed
echo "Checking required packages..."
pip install -q selenium webdriver-manager

# Run the Python script with error handling
echo "Running voting script..."
python3 vote_automation.py

# Check if the script executed successfully
if [ $? -eq 0 ]; then
    echo "Script executed successfully!"
else
    echo "Script encountered errors. Check the voting_log.log file for details."
fi

# Deactivate the virtual environment
echo "Deactivating virtual environment..."
deactivate

echo "Script execution completed!"
