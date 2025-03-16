#!/bin/bash

# Script to build and run the appointment bot in Docker

echo "Building Docker image..."
docker-compose build

echo "Starting Docker container..."
docker-compose up -d

echo "Container started. To view logs, run:"
echo "docker-compose logs -f"

echo "To stop the container, run:"
echo "docker-compose down"
