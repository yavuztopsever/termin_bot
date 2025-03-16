#!/bin/bash

# Script to stop the running application and clean up

echo "Stopping any running application..."

# Find and kill the Node.js process
pkill -f "node.*src/index.ts" || echo "No running Node.js process found"

# Stop Docker container if running
if docker ps | grep -q termin-bot; then
  echo "Stopping Docker container..."
  docker-compose down
else
  echo "No Docker container running"
fi

echo "Application stopped successfully"
