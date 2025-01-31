#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting end-to-end test...${NC}"

# Check if image path is provided
if [ "$#" -ne 1 ]; then
    echo -e "${RED}Error: Please provide an image path${NC}"
    echo "Usage: $0 <image_path>"
    exit 1
fi

IMAGE_PATH=$1

# Check if image exists
if [ ! -f "$IMAGE_PATH" ]; then
    echo -e "${RED}Error: Image file not found: $IMAGE_PATH${NC}"
    exit 1
fi

# Ensure services are running
echo -e "${YELLOW}Ensuring services are running...${NC}"
docker-compose ps | grep "Up" > /dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Starting services...${NC}"
    docker-compose up -d
    
    # Wait for services to be ready
    echo -e "${YELLOW}Waiting for services to be ready...${NC}"
    sleep 10
fi

# Run the test
echo -e "${YELLOW}Running upscale test...${NC}"
python3 tests/e2e/test_upscale.py "$IMAGE_PATH"

# Check the result
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Test completed successfully!${NC}"
    exit 0
else
    echo -e "${RED}Test failed!${NC}"
    exit 1
fi
