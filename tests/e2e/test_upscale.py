#!/usr/bin/env python3
import os
import sys
import time
import requests
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from PIL import Image
import io

class WebhookHandler(BaseHTTPRequestHandler):
    received_images = []
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        image_data = self.read(content_length)
        
        # Store the received image
        WebhookHandler.received_images.append(image_data)
        
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

def start_webhook_server(port=8080):
    server = HTTPServer(('localhost', port), WebhookHandler)
    thread = Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    return server

def test_image_upscale(image_path):
    print("Starting end-to-end test for image upscaling...")
    
    # Start webhook server
    webhook_port = 8080
    webhook_server = start_webhook_server(webhook_port)
    webhook_url = f"http://localhost:{webhook_port}"
    print(f"Started webhook server at {webhook_url}")
    
    try:
        # Upload image for processing
        print("Uploading image for processing...")
        with open(image_path, 'rb') as f:
            response = requests.post(
                "http://localhost:8000/upscale",
                files={'image': f},
                data={'webhook_url': webhook_url}
            )
        
        if response.status_code != 200:
            print(f"Error: Upload failed with status {response.status_code}")
            print(response.text)
            return False
        
        task_data = response.json()
        task_id = task_data['task_id']
        print(f"Task ID: {task_id}")
        
        # Wait for webhook to receive the processed image
        max_wait = 300  # 5 minutes
        start_time = time.time()
        while not WebhookHandler.received_images and time.time() - start_time < max_wait:
            time.sleep(1)
            print(".", end="", flush=True)
        
        if not WebhookHandler.received_images:
            print("\nError: Timeout waiting for processed image")
            return False
        
        print("\nReceived processed image!")
        
        # Save and analyze the processed image
        processed_image_path = os.path.join(
            os.path.dirname(image_path),
            "processed_" + os.path.basename(image_path)
        )
        
        with open(processed_image_path, 'wb') as f:
            f.write(WebhookHandler.received_images[0])
        
        # Verify the processed image
        original = Image.open(image_path)
        processed = Image.open(processed_image_path)
        
        # Check if the processed image is larger (upscaled)
        if processed.size[0] <= original.size[0] or processed.size[1] <= original.size[1]:
            print("Error: Processed image is not upscaled")
            return False
        
        print(f"Success! Original size: {original.size}, Processed size: {processed.size}")
        print(f"Processed image saved to: {processed_image_path}")
        return True
        
    finally:
        webhook_server.shutdown()
        webhook_server.server_close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_upscale.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    if not os.path.exists(image_path):
        print(f"Error: Image file not found: {image_path}")
        sys.exit(1)
    
    success = test_image_upscale(image_path)
    sys.exit(0 if success else 1)
