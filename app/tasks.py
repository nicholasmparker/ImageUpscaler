import logging
import os
import time

import httpx
from fastapi import UploadFile
from redis.asyncio import Redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def process_image(
    image_data: bytes, content_type: str, redis: Redis, task_id: str
) -> None:
    """Process the image using Real-ESRGAN service"""
    logger.info(f"Starting background processing for task {task_id}")
    start_time = time.time()

    try:
        # Update status to processing
        await redis.hset(f"task:{task_id}", "status", "processing")
        logger.info(
            f"Task {task_id}: Status updated to processing in {time.time() - start_time:.2f}s"
        )

        logger.info(
            f"Task {task_id}: Processing image data, size: {len(image_data)} bytes"
        )

        # Send to ESRGAN service
        logger.info(f"Task {task_id}: Sending to ESRGAN service")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://esrgan:8001/upscale",
                content=image_data,
                headers={"Content-Type": content_type or "image/jpeg"},
                timeout=float(os.getenv("REQUEST_TIMEOUT", "300")),
            )
            response.raise_for_status()
            logger.info(
                f"Task {task_id}: ESRGAN processing complete in {time.time() - start_time:.2f}s"
            )

            # Store result in Redis
            await redis.set(f"result:{task_id}", response.content)
            await redis.hset(f"task:{task_id}", "status", "completed")
            logger.info(
                f"Task {task_id}: Result stored in Redis in {time.time() - start_time:.2f}s"
            )

    except Exception as e:
        error_msg = (
            f"Task {task_id} failed after {time.time() - start_time:.2f}s: {str(e)}"
        )
        logger.error(error_msg)
        await redis.hset(f"task:{task_id}", "status", f"error: {str(e)}")


async def process_image_background(
    image: UploadFile, redis: Redis, task_id: str
) -> None:
    """Process the image using Real-ESRGAN service in the background"""
    logger.info(f"Starting background processing for task {task_id}")
    start_time = time.time()

    try:
        # Update status to processing
        await redis.hset(f"task:{task_id}", "status", "processing")
        logger.info(
            f"Task {task_id}: Status updated to processing in {time.time() - start_time:.2f}s"
        )

        # Read image data
        image_data = await image.read()
        logger.info(f"Task {task_id}: Read image data, size: {len(image_data)} bytes")

        # Send to ESRGAN service
        logger.info(f"Task {task_id}: Sending to ESRGAN service")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://esrgan:8001/upscale",
                content=image_data,
                headers={"Content-Type": image.content_type or "image/jpeg"},
                timeout=float(os.getenv("REQUEST_TIMEOUT", "300")),
            )
            response.raise_for_status()
            logger.info(
                f"Task {task_id}: ESRGAN processing complete in {time.time() - start_time:.2f}s"
            )

            # Store result in Redis
            await redis.set(f"result:{task_id}", response.content)
            await redis.hset(f"task:{task_id}", "status", "completed")
            logger.info(
                f"Task {task_id}: Result stored in Redis in {time.time() - start_time:.2f}s"
            )

    except Exception as e:
        error_msg = (
            f"Task {task_id} failed after {time.time() - start_time:.2f}s: {str(e)}"
        )
        logger.error(error_msg)
        await redis.hset(f"task:{task_id}", "status", f"error: {str(e)}")
