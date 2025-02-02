import os
from typing import Dict, List

import httpx
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from redis.asyncio import Redis

from app.tasks import process_image

app = FastAPI(
    title="Image Upscaler API",
    description="A FastAPI service for upscaling images using Real-ESRGAN",
    version="1.0.0",
)

# Simple Redis connection
redis = Redis(
    host=os.environ.get("REDIS_HOST", "redis"),
    port=int(os.environ.get("REDIS_PORT", "6379")),
    password=os.environ.get("REDIS_PASSWORD", ""),
    decode_responses=False,  # Keep binary data for image results
)


class ApiInfo(BaseModel):
    message: str
    version: str
    endpoints: Dict[str, str]


class TaskResponse(BaseModel):
    task_id: str


class TaskStatus(BaseModel):
    task_id: str
    status: str
    created_at: str


class JobList(BaseModel):
    jobs: List[TaskStatus]


@app.get("/", response_model=ApiInfo)
async def root():
    """
    Root endpoint that returns API information and available endpoints.

    Returns:
        dict: API information including version and available endpoints

    Example response:
        {
            "message": "Welcome to the Image Upscaler API",
            "version": "1.0.0",
            "endpoints": {
                "/": "This help message",
                "/upscale": "Synchronously upscale an image",
                "/upscale/async": "Asynchronously upscale an image",
                "/status/{task_id}": "Check status of async upscale task",
                "/result/{task_id}": "Get result of completed task",
                "/jobs": "List all jobs"
            }
        }
    """
    return {
        "message": "Welcome to the Image Upscaler API",
        "version": "1.0.0",
        "endpoints": {
            "/": "This help message",
            "/upscale": "Synchronously upscale an image",
            "/upscale/async": "Asynchronously upscale an image",
            "/status/{task_id}": "Check status of async upscale task",
            "/result/{task_id}": "Get result of completed task",
            "/jobs": "List all jobs",
        },
    }


@app.post("/upscale")
async def upscale_image_sync(image: UploadFile) -> Response:
    """
    Synchronously upscale an image. This endpoint will block until the image is processed.

    Args:
        image: The image file to upscale

    Returns:
        Response: The upscaled image in JPEG format

    Raises:
        HTTPException(400): If no file is uploaded
        HTTPException(500): If there's an error processing the image
    """
    if not image:
        raise HTTPException(400, "No file uploaded")

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
            return Response(content=response.content, media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(500, str(e)) from e


@app.post("/upscale/async", response_model=TaskResponse)
async def upscale_image_async(image: UploadFile) -> Dict[str, str]:
    """
    Asynchronously upscale an image. Returns immediately with a task ID.

    Args:
        image: The image file to upscale

    Returns:
        dict: Contains the task_id for checking status

    Raises:
        HTTPException(400): If no file is uploaded
        HTTPException(500): If there's an error queuing the task

    Example response:
        {
            "task_id": "123e4567-e89b-12d3-a456-426614174000"
        }
    """
    if not image:
        raise HTTPException(400, "No file uploaded")

    try:
        # Process image and get task ID
        task_id = await process_image(image, redis)
        return {"task_id": task_id}
    except Exception as e:
        raise HTTPException(500, str(e)) from e


@app.get("/status/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str) -> Dict[str, str]:
    """
    Get the status of an upscaling task.

    Args:
        task_id: The ID of the task to check

    Returns:
        dict: Task status information

    Raises:
        HTTPException(404): If the task is not found

    Example response:
        {
            "task_id": "123e4567-e89b-12d3-a456-426614174000",
            "status": "completed",
            "created_at": "2024-02-02T10:30:00"
        }
    """
    task_info = await redis.hgetall(f"task:{task_id}")
    if not task_info:
        raise HTTPException(404, "Task not found")

    return {
        "task_id": task_id,
        "status": task_info.get(b"status", b"unknown").decode(),
        "created_at": task_info.get(b"created_at", b"").decode(),
    }


@app.get("/result/{task_id}")
async def get_task_result(task_id: str) -> Response:
    """
    Get the result of a completed upscaling task.

    Args:
        task_id: The ID of the completed task

    Returns:
        Response: The upscaled image in JPEG format

    Raises:
        HTTPException(404): If the task or result is not found
        HTTPException(400): If the task is not completed
    """
    task_info = await redis.hgetall(f"task:{task_id}")
    if not task_info:
        raise HTTPException(404, "Task not found")

    status = task_info.get(b"status", b"unknown").decode()
    if status != "completed":
        raise HTTPException(400, f"Task is not completed. Status: {status}")

    result = await redis.get(f"result:{task_id}")
    if not result:
        raise HTTPException(404, "Result not found")

    return Response(content=result, media_type="image/jpeg")


@app.get("/jobs", response_model=JobList)
async def list_jobs() -> Dict[str, List[Dict[str, str]]]:
    """
    List all upscaling jobs in the system.

    Returns:
        dict: List of all jobs with their status

    Example response:
        {
            "jobs": [
                {
                    "task_id": "123e4567-e89b-12d3-a456-426614174000",
                    "status": "completed",
                    "created_at": "2024-02-02T10:30:00"
                }
            ]
        }
    """
    jobs = []
    async for key in redis.scan_iter("task:*"):
        task_id = key.decode().split(":", 1)[1]
        task_info = await redis.hgetall(key)
        jobs.append(
            {
                "task_id": task_id,
                "status": task_info.get(b"status", b"unknown").decode(),
                "created_at": task_info.get(b"created_at", b"").decode(),
            }
        )
    return {"jobs": jobs}


@app.get("/health")
def health_check():
    """
    Health check endpoint.

    Returns:
        dict: Simple status response

    Example response:
        {
            "status": "ok"
        }
    """
    return {"status": "ok"}
