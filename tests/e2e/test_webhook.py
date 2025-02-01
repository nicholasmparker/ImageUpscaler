#!/usr/bin/env python3
import io
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
from PIL import Image

# Global flag to track if webhook was received
webhook_received = False
processed_image = None


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        global webhook_received, processed_image
        content_length = int(self.headers["Content-Length"])
        content_type = self.headers.get("Content-Type", "")

        # Read raw binary data
        image_data = self.rfile.read(content_length)

        if content_type == "image/jpeg":
            try:
                # Store the received image
                processed_image = Image.open(io.BytesIO(image_data))
                webhook_received = True
                self.send_response(200)
            except Exception as e:
                print(f"Error processing image: {e}")
                self.send_response(400)
        else:
            print(f"Unexpected content type: {content_type}")
            self.send_response(400)

        self.end_headers()


def start_webhook_server(host, port):
    server = HTTPServer((host, port), WebhookHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    return server


def test_webhook_upscale(image_path, wait_for_webhook=False):
    print("Starting webhook test for image upscaling...")

    # Get configuration from environment
    webhook_host = os.getenv("WEBHOOK_HOST", "0.0.0.0")
    webhook_port = int(os.getenv("WEBHOOK_PORT", "9090"))
    api_host = os.getenv("API_HOST", "localhost")
    api_port = os.getenv("API_PORT", "8000")

    # Start webhook server
    webhook_server = start_webhook_server(webhook_host, webhook_port)

    # Use container name for webhook URL when running in Docker
    webhook_url = f"http://{webhook_host}:{webhook_port}"
    api_url = f"http://{api_host}:{api_port}/upscale"

    try:
        # Upload image for processing
        print(f"Uploading image to {api_url}...")
        with open(image_path, "rb") as f:
            response = requests.post(
                f"{api_url}?webhook_url={webhook_url}", files={"image": f}
            )

        if response.status_code != 200:
            print(f"Error: Upload failed with status {response.status_code}")
            print(response.text)
            return False

        # Get task ID from response
        task_id = response.json()["task_id"]
        print(f"Task ID: {task_id}")

        if not wait_for_webhook:
            print("Task submitted successfully. Not waiting for webhook.")
            return True

        print("Image processing started. Waiting for webhook callback...")

        # Wait for webhook
        timeout = 30
        start_time = time.time()
        while not webhook_received and (time.time() - start_time) < timeout:
            time.sleep(1)

        if not webhook_received:
            print("Error: Webhook not received within timeout")
            return False

        # Verify the processed image
        if processed_image:
            original_img = Image.open(image_path)
            if (
                processed_image.size[0] <= original_img.size[0]
                or processed_image.size[1] <= original_img.size[1]
            ):
                print(
                    f"Error: Image not upscaled. Original size: {original_img.size}, New size: {processed_image.size}"
                )
                return False
            print(
                f"Image successfully upscaled from {original_img.size} to {processed_image.size}"
            )

            # Save the processed image
            output_path = os.path.join(
                os.path.dirname(image_path),
                "webhook_processed_" + os.path.basename(image_path),
            )
            processed_image.save(output_path)
            print(f"Saved processed image to {output_path}")
            return True

    finally:
        webhook_server.shutdown()
        webhook_server.server_close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_webhook.py <image_path> [--wait-for-webhook]")
        sys.exit(1)

    wait_for_webhook = "--wait-for-webhook" in sys.argv
    success = test_webhook_upscale(sys.argv[1], wait_for_webhook)
    sys.exit(0 if success else 1)
