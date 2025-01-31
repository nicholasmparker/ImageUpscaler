#!/bin/bash

# Default to CPU mode if not specified
export USE_GPU=${USE_GPU:-false}

# Choose the appropriate compose file based on GPU mode
if [ "$USE_GPU" = "true" ]; then
    echo "Starting in GPU mode..."
    docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up --build
else
    echo "Starting in CPU mode..."
    docker-compose up --build
fi
