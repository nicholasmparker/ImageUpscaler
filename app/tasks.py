import os
import uuid
from datetime import datetime

import httpx
from fastapi import UploadFile
from redis.asyncio import Redis


async def process_image(image: UploadFile, redis: Redis) -> str:
    """Process the image using Real-ESRGAN service"""
    task_id = str(uuid.uuid4())

    # Store task info in Redis
    await redis.hset(
        f"task:{task_id}",
        mapping={
            "status": "processing",
            "created_at": datetime.utcnow().isoformat(),
        },
    )

    try:
        # Read image data
        image_data = await image.read()

        # Send to ESRGAN service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://esrgan:8001/upscale",
                content=image_data,
                headers={"Content-Type": image.content_type or "image/jpeg"},
                timeout=float(os.getenv("REQUEST_TIMEOUT", "300")),
            )
            response.raise_for_status()

            # Store result in Redis
            await redis.set(f"result:{task_id}", response.content)
            await redis.hset(f"task:{task_id}", "status", "completed")

    except Exception as e:
        await redis.hset(f"task:{task_id}", "status", f"error: {str(e)}")
        raise

    return task_id
