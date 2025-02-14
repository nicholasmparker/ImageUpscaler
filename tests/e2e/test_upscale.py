#!/usr/bin/env python3
import io
import os
import time

import pytest
import requests
from PIL import Image


@pytest.fixture
def image_path():
    return "tests/e2e/images/bird.jpg"


def test_image_upscale_sync(image_path):
    """End-to-end test for synchronous image upscaling"""
    print("Starting end-to-end test for synchronous image upscaling...")

    # Get API host and port from environment or use defaults
    api_host = os.environ.get("API_HOST", "localhost")
    api_port = os.environ.get("API_PORT", "8000")
    api_url = f"http://{api_host}:{api_port}/upscale"

    # Upload image for processing
    print(f"Uploading image to {api_url}...")
    try:
        with open(image_path, "rb") as f:
            image_data = f.read()
            print(f"Read image data, size: {len(image_data)} bytes")
            files = {"image": ("bird.jpg", image_data, "image/jpeg")}
            print("Sending request...")
            response = requests.post(api_url, files=files, timeout=300)
            print(f"Request completed with status: {response.status_code}")

            if response.status_code != 200:
                print(f"Error: Upload failed with status {response.status_code}")
                print(f"Response headers: {response.headers}")
                print(f"Response: {response.text}")
                raise Exception("Upload failed")

            # Save and verify the result
            processed_image = Image.open(io.BytesIO(response.content))
            output_path = "tests/e2e/images/upscaled_bird_sync.jpg"
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

    except Exception as e:
        print(f"Test failed: {str(e)}")
        raise


def test_image_upscale_async(image_path):
    """End-to-end test for asynchronous image upscaling"""
    print("Starting end-to-end test for async image upscaling...")

    # Get API host and port from environment or use defaults
    api_host = os.environ.get("API_HOST", "localhost")
    api_port = os.environ.get("API_PORT", "8000")
    api_url = f"http://{api_host}:{api_port}/upscale/async"

    # Upload image for processing
    print(f"Uploading image to {api_url}...")
    try:
        with open(image_path, "rb") as f:
            image_data = f.read()
            print(f"Read image data, size: {len(image_data)} bytes")
            start_upload = time.time()
            files = {"image": ("bird.jpg", image_data, "image/jpeg")}
            print("Sending request...")
            response = requests.post(api_url, files=files)
            upload_time = time.time() - start_upload
            print(
                f"Request completed with status: {response.status_code} in {upload_time:.2f} seconds"
            )

            if response.status_code != 200:
                print(f"Error: Upload failed with status {response.status_code}")
                print(f"Response headers: {response.headers}")
                print(f"Response: {response.text}")
                raise Exception("Upload failed")

            # Get task ID from response
            task_id = response.json()["task_id"]
            print(f"Task ID: {task_id}")

            # Poll status endpoint until complete
            status_url = f"http://{api_host}:{api_port}/status/{task_id}"
            timeout = 600  # 10 minutes
            start_time = time.time()
            poll_count = 0

            while time.time() - start_time < timeout:
                poll_count += 1
                status_response = requests.get(status_url)
                if status_response.status_code != 200:
                    raise Exception(f"Failed to get status: {status_response.text}")

                status = status_response.json()["status"]
                elapsed = time.time() - start_time
                print(f"Poll {poll_count}: Task status after {elapsed:.2f}s: {status}")

                if status == "completed":
                    break
                elif status.startswith("error"):
                    raise Exception(f"Task failed: {status}")

                time.sleep(5)  # Wait 5 seconds before polling again
            else:
                raise Exception("Task timed out")

            # Get the result
            result_url = f"http://{api_host}:{api_port}/result/{task_id}"
            result_response = requests.get(result_url)
            if result_response.status_code != 200:
                raise Exception(f"Failed to get result: {result_response.text}")

            # Save and verify the result
            processed_image = Image.open(io.BytesIO(result_response.content))
            output_path = "tests/e2e/images/upscaled_bird_async.jpg"
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

    except Exception as e:
        print(f"Test failed: {str(e)}")
        raise


def test_list_jobs(image_path):
    """Test listing all jobs"""
    print("Starting test for listing jobs...")

    # Get API host and port from environment or use defaults
    api_host = os.environ.get("API_HOST", "localhost")
    api_port = os.environ.get("API_PORT", "8000")
    jobs_url = f"http://{api_host}:{api_port}/jobs"

    try:
        # First submit an async job
        api_url = f"http://{api_host}:{api_port}/upscale/async"
        with open(image_path, "rb") as f:
            image_data = f.read()
            files = {"image": ("bird.jpg", image_data, "image/jpeg")}
            response = requests.post(api_url, files=files)
            print(f"Job submission response: {response.status_code}")
            if response.status_code != 200:
                print(f"Response text: {response.text}")
                raise Exception("Failed to submit job")
            task_id = response.json()["task_id"]
            print(f"Submitted task ID: {task_id}")

        # Wait a bit for the job to be processed
        time.sleep(2)

        # Get the list of jobs
        jobs_response = requests.get(jobs_url)
        print(f"Jobs list response: {jobs_response.status_code}")
        if jobs_response.status_code != 200:
            print(f"Response text: {jobs_response.text}")
            raise Exception("Failed to get jobs list")

        jobs = jobs_response.json()["jobs"]
        print(f"Found {len(jobs)} jobs")

        # Verify our job is in the list
        found = False
        for job in jobs:
            if job["task_id"] == task_id:
                found = True
                print(f"Found our job with status: {job['status']}")
                break

        assert found, f"Submitted task {task_id} not found in jobs list"
        print("Test completed successfully!")

    except Exception as e:
        print(f"Test failed: {str(e)}")
        raise
