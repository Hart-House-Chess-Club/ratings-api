#!/bin/bash
# filepath: /Users/victorzheng/Documents/fide-api/fide-api/start_updater_service.sh

# This script starts the rating list updater service in the background

echo "Starting rating list updater service..."

# Make sure we're in the project directory
cd "$(dirname "$0")"

# Run the updater script in the background
nohup python -m src.scraper.ratinglists.updater > ./rating_updater.log 2>&1 &

# Save the process ID
echo $! > ./rating_updater.pid

echo "Rating list updater service started with PID $(cat ./rating_updater.pid)"
echo "Log file is at ./rating_updater.log"
