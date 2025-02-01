#!/usr/bin/env python3
import os

import pytest
import requests
from PIL import Image


@pytest.fixture
def image_path():
    return "tests/e2e/images/bird.jpg"


def test_image_upscale(image_path):
    print("Starting end-to-end test for image upscaling...")

    # Get API host and port from environment or use defaults
    api_host = os.environ.get("API_HOST", "localhost")
    api_port = os.environ.get("API_PORT", "8000")
    api_url = f"http://{api_host}:{api_port}/upscale/sync"

    # Upload image for processing
    print(f"Uploading image to {api_url}...")
    with open(image_path, "rb") as f:
        response = requests.post(api_url, files={"image": f})

    if response.status_code != 200:
        print(f"Error: Upload failed with status {response.status_code}")
        print(f"Response: {response.text}")
        raise Exception("Upload failed")

    # Save the processed image
    print("Saving processed image...")
    processed_image = Image.open(response.raw)
    output_path = "tests/e2e/images/upscaled_bird.jpg"
    processed_image.save(output_path)

    # Verify the processed image is larger
    original_image = Image.open(image_path)
    assert (
        processed_image.size[0] > original_image.size[0]
    ), "Processed image should be larger"
    assert (
        processed_image.size[1] > original_image.size[1]
    ), "Processed image should be larger"

    print("Test completed successfully!")
