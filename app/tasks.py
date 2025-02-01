import uuid

import requests
from fastapi import UploadFile


async def process_image(image: UploadFile, webhook_url: str, redis_client):
    """Process the image using Real-ESRGAN service and send result to webhook"""
    task_id = str(uuid.uuid4())

    # Store task info in Redis
    redis_client.hset(
        f"task:{task_id}", mapping={"status": "processing", "webhook_url": webhook_url}
    )

    try:
        # Read image data and content type
        image_data = await image.read()
        content_type = image.content_type or "image/jpeg"

        # Send to ESRGAN service with proper content type
        headers = {"Content-Type": content_type}
        response = requests.post(
            "http://esrgan:8001/upscale", data=image_data, headers=headers
        )
        response.raise_for_status()

        # Send the upscaled image to webhook as raw binary
        headers = {"Content-Type": "image/jpeg"}
        webhook_response = requests.post(
            webhook_url, data=response.content, headers=headers
        )
        webhook_response.raise_for_status()

        redis_client.hset(f"task:{task_id}", "status", "completed")
    except Exception as e:
        redis_client.hset(f"task:{task_id}", "status", f"error: {str(e)}")
        raise

    return task_id
