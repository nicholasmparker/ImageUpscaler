#!/usr/bin/env python3
import os
import requests
from PIL import Image
import io

def test_image_upscale(image_path):
    print("Starting end-to-end test for image upscaling...")
    
    # Get API host and port from environment or use defaults
    api_host = os.environ.get('API_HOST', 'localhost')
    api_port = os.environ.get('API_PORT', '8000')
    api_url = f"http://{api_host}:{api_port}/upscale/sync"
    
    # Upload image for processing
    print(f"Uploading image to {api_url}...")
    with open(image_path, 'rb') as f:
        response = requests.post(
            api_url,
            files={'image': f}
        )
    
    if response.status_code != 200:
        print(f"Error: Upload failed with status {response.status_code}")
        print(response.text)
        return False
    
    # Save the processed image
    processed_image_path = os.path.join(
        os.path.dirname(image_path),
        "processed_" + os.path.basename(image_path)
    )
    
    with open(processed_image_path, 'wb') as f:
        f.write(response.content)
    
    # Verify the processed image
    try:
        with Image.open(processed_image_path) as img:
            # Check if image dimensions are larger (upscaled)
            original_img = Image.open(image_path)
            if img.size[0] <= original_img.size[0] or img.size[1] <= original_img.size[1]:
                print(f"\nError: Image not upscaled. Original size: {original_img.size}, New size: {img.size}")
                return False
            print(f"\nImage successfully upscaled from {original_img.size} to {img.size}")
    except Exception as e:
        print(f"\nError: Failed to verify processed image: {e}")
        return False
    
    return True

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python test_upscale.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    success = test_image_upscale(image_path)
    sys.exit(0 if success else 1)
