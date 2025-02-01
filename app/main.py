import os

import redis
import requests
from fastapi import FastAPI, HTTPException, Response, UploadFile

from .models import UpscaleResponse
from .tasks import process_image

app = FastAPI(title="Image Upscaler API")

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True,
)


def process_image_sync(image_data: bytes) -> bytes:
    """Process an image synchronously using the ESRGAN service."""
    esrgan_host = os.getenv("ESRGAN_HOST", "localhost")
    esrgan_port = os.getenv("ESRGAN_PORT", "8001")

    # Send image to ESRGAN service
    response = requests.post(
        f"http://{esrgan_host}:{esrgan_port}/upscale", files={"image": image_data}
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=500, detail="ESRGAN service failed to process image"
        )

    return response.content


@app.post("/upscale", response_model=UpscaleResponse)
async def upscale_image(image: UploadFile, webhook_url: str):
    """
    Upload an image for upscaling.
    The processed image will be sent to the webhook_url when complete.
    """
    if not image.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")

    # Store the image and queue the task
    task_id = await process_image(image, webhook_url, redis_client)

    return UpscaleResponse(task_id=task_id, status="processing")


@app.post("/upscale/sync")
async def upscale_image_sync(image: UploadFile):
    """Synchronous endpoint that returns the processed image directly."""
    # Read image data
    image_data = await image.read()

    # Process image
    try:
        processed_image = process_image_sync(image_data)
        return Response(content=processed_image, media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
