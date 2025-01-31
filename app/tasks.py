import uuid
from fastapi import UploadFile
import requests


async def process_image(image: UploadFile, webhook_url: str, redis_client):
    """Process the image using Real-ESRGAN service and send result to webhook"""
    task_id = str(uuid.uuid4())

    # Store task info in Redis
    redis_client.hset(
        f"task:{task_id}", mapping={"status": "processing", "webhook_url": webhook_url}
    )

    try:
        # Send to ESRGAN service
        files = {"image": await image.read()}
        response = requests.post("http://esrgan:8001/upscale", files=files)
        response.raise_for_status()

        # Send the upscaled image to webhook
        webhook_response = requests.post(webhook_url, files={"image": response.content})
        webhook_response.raise_for_status()

        redis_client.hset(f"task:{task_id}", "status", "completed")
    except Exception as e:
        redis_client.hset(f"task:{task_id}", "status", f"error: {str(e)}")
        raise

    return task_id
