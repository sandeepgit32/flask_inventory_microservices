#!/bin/bash
# Database Seed Script Runner
# 
# This script sets up the environment and runs the Python seed script.
#
# Usage:
#   ./seed.sh                    # Use default settings (connects to localhost:32000)
#   ./seed.sh --clear-only       # Only clear data
#   ./seed.sh --help             # Show all options

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is required but not installed."
    exit 1
fi

# Check if required packages are installed
echo "Checking dependencies..."
python3 -c "import mysql.connector" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing mysql-connector-python..."
    pip3 install mysql-connector-python
fi

python3 -c "from faker import Faker" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing faker..."
    pip3 install faker
fi

# Load environment variables from .env if it exists
if [ -f "$SCRIPT_DIR/../.env" ]; then
    echo "Loading environment from .env..."
    export $(grep -v '^#' "$SCRIPT_DIR/../.env" | xargs)
fi

# Run the seed script
echo ""
python3 "$SCRIPT_DIR/seed_data.py" "$@"
