import os

import redis
import requests
from fastapi import FastAPI, HTTPException, Response, UploadFile

from .models import UpscaleResponse
from .tasks import process_image

app = FastAPI(title="Image Upscaler API")

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "truenas.chickenmilkbomb.com"),
    port=int(os.getenv("REDIS_PORT", 30036)),
    password=os.getenv("REDIS_PASSWORD", "1d3pdn"),
    decode_responses=True,
)


def process_image_sync(image_data: bytes, content_type: str) -> bytes:
    """Process an image synchronously using the ESRGAN service."""
    esrgan_host = os.getenv("ESRGAN_HOST", "localhost")
    esrgan_port = os.getenv("ESRGAN_PORT", "8001")

    # Send image to ESRGAN service with proper content type
    headers = {"Content-Type": content_type}
    response = requests.post(
        f"http://{esrgan_host}:{esrgan_port}/upscale", data=image_data, headers=headers
    )

    if response.status_code == 400:
        raise HTTPException(
            status_code=400, detail="Invalid image format or corrupted image data"
        )
    elif response.status_code == 413:
        raise HTTPException(status_code=413, detail="Image size too large")
    elif response.status_code != 200:
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
    # Check if file is provided
    if not image:
        raise HTTPException(400, "No file uploaded")

    # Check content type if available
    if image.content_type and not image.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")

    # Store the image and queue the task
    task_id = await process_image(image, webhook_url, redis_client)

    return UpscaleResponse(task_id=task_id, status="processing")


@app.post("/upscale/sync")
async def upscale_image_sync(image: UploadFile):
    """
    Synchronous endpoint that returns the processed image directly.

    Returns:
        Response: The upscaled image as a binary response with image/jpeg content type

    Raises:
        400: If no file is uploaded or if the file is not an image
        413: If the image is too large
        500: If the ESRGAN service fails to process the image
    """
    # Validate input
    if not image:
        raise HTTPException(400, "No file uploaded")

    if not image.content_type:
        raise HTTPException(400, "Content-Type header required")

    if not image.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")

    # Read and process image
    try:
        image_data = await image.read()
        processed_image = process_image_sync(image_data, image.content_type)
        return Response(
            content=processed_image,
            media_type="image/jpeg",
            headers={"X-Original-Content-Type": image.content_type},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Internal server error while processing image"
        ) from e
