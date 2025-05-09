#!/bin/bash
# Script to set up and run the Kagent frontend

set -e  # Exit on error

echo "=== KAGENT FRONTEND SETUP ==="
echo "This script will set up and run the Kagent frontend"

# Navigate to the frontend directory
cd frontend

# Check if node is installed
if ! command -v node &> /dev/null; then
    echo "Node.js is not installed. Please install Node.js to continue."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "npm is not installed. Please install npm to continue."
    exit 1
fi

# Install dependencies
echo -e "\n=== Installing dependencies ==="
npm install

# Start the development server
echo -e "\n=== Starting development server ==="
npm start 