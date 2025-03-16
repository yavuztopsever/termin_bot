#!/bin/bash

# Script to run the API validation tool

echo "Starting API validation..."
npx ts-node src/validateApi.ts

echo "API validation complete. Check the debug directory for results."
