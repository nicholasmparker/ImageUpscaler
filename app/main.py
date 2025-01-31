from fastapi import FastAPI, UploadFile, HTTPException
import redis
import os
from .tasks import process_image
from .models import UpscaleResponse

app = FastAPI(title="Image Upscaler API")

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True,
)


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
