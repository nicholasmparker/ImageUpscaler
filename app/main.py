import os
from typing import Dict, List

import httpx
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel, Field
from redis.asyncio import Redis

from app.tasks import process_image

app = FastAPI(
    title="Image Upscaler API",
    description="""
    A FastAPI service for upscaling images using Real-ESRGAN.
    
    ## Features
    - Synchronous and asynchronous image upscaling
    - Support for various image formats
    - Task status tracking
    - Job management
    
    ## Usage
    1. Upload an image using `/upscale` (sync) or `/upscale/async` (async)
    2. For async uploads, use `/status/{task_id}` to check progress
    3. Once complete, get the result using `/result/{task_id}`
    
    ## Notes
    - Maximum image size: 10MB
    - Supported formats: JPEG, PNG
    - Processing time varies based on image size
    """,
    version="1.0.0",
    contact={
        "name": "Image Upscaler Team",
        "url": "https://github.com/nicholasmparker/imageupscaler",
    },
    license_info={
        "name": "MIT",
    },
)

# Simple Redis connection
redis = Redis(
    host=os.environ.get("REDIS_HOST", "redis"),
    port=int(os.environ.get("REDIS_PORT", "6379")),
    password=os.environ.get("REDIS_PASSWORD", ""),
    decode_responses=False,  # Keep binary data for image results
)


class ApiInfo(BaseModel):
    message: str = Field(..., description="Welcome message")
    version: str = Field(..., description="API version number")
    endpoints: Dict[str, str] = Field(
        ..., description="Available endpoints and their descriptions"
    )

    class Config:
        schema_extra = {
            "example": {
                "message": "Welcome to the Image Upscaler API",
                "version": "1.0.0",
                "endpoints": {
                    "/": "This help message",
                    "/upscale": "Synchronously upscale an image",
                    "/upscale/async": "Asynchronously upscale an image",
                },
            }
        }


class TaskResponse(BaseModel):
    task_id: str = Field(..., description="Unique identifier for the upscaling task")

    class Config:
        schema_extra = {"example": {"task_id": "123e4567-e89b-12d3-a456-426614174000"}}


class TaskStatus(BaseModel):
    task_id: str = Field(..., description="Unique identifier for the upscaling task")
    status: str = Field(
        ...,
        description="Current status of the task (pending, processing, completed, failed)",
    )
    created_at: str = Field(..., description="Timestamp when the task was created")

    class Config:
        schema_extra = {
            "example": {
                "task_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "completed",
                "created_at": "2024-02-02T10:30:00",
            }
        }


class JobList(BaseModel):
    jobs: List[TaskStatus] = Field(..., description="List of all upscaling tasks")

    class Config:
        schema_extra = {
            "example": {
                "jobs": [
                    {
                        "task_id": "123e4567-e89b-12d3-a456-426614174000",
                        "status": "completed",
                        "created_at": "2024-02-02T10:30:00",
                    }
                ]
            }
        }


@app.get("/", response_model=ApiInfo, tags=["Info"])
async def root():
    """
    Get API information and available endpoints.

    Returns a welcome message, API version, and list of available endpoints with their descriptions.
    This is useful for getting an overview of the API's capabilities.
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


@app.post("/upscale", tags=["Upscaling"])
async def upscale_image_sync(
    image: UploadFile = File(..., description="Image file to upscale")
) -> Response:
    """
    Synchronously upscale an image.

    This endpoint will process the image immediately and return the result. It may take several
    minutes depending on the image size. For large images, consider using the async endpoint.

    - **Input**: Image file (JPEG or PNG)
    - **Output**: Upscaled image in JPEG format
    - **Processing**: 4x upscaling using Real-ESRGAN

    The request will timeout after the configured REQUEST_TIMEOUT (default: 300 seconds).
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


@app.post("/upscale/async", response_model=TaskResponse, tags=["Upscaling"])
async def upscale_image_async(
    image: UploadFile = File(..., description="Image file to upscale")
) -> Dict[str, str]:
    """
    Asynchronously upscale an image.

    This endpoint immediately returns a task ID and processes the image in the background.
    Recommended for larger images or when you don't want to wait for immediate results.

    ## Process Flow:
    1. Upload image and receive task_id
    2. Check task status using `/status/{task_id}`
    3. Once status is "completed", get result using `/result/{task_id}`

    ## Notes:
    - Task IDs expire after 24 hours
    - Failed tasks will be marked with status "failed"
    """
    if not image:
        raise HTTPException(400, "No file uploaded")

    try:
        # Process image and get task ID
        task_id = await process_image(image, redis)
        return {"task_id": task_id}
    except Exception as e:
        raise HTTPException(500, str(e)) from e


@app.get("/status/{task_id}", response_model=TaskStatus, tags=["Task Management"])
async def get_task_status(task_id: str) -> Dict[str, str]:
    """
    Get the status of an upscaling task.

    ## Status Values:
    - **pending**: Task is queued
    - **processing**: Task is being processed
    - **completed**: Task is complete, result available
    - **failed**: Task failed to process

    Use this endpoint to poll for task completion before requesting the result.
    """
    task_info = await redis.hgetall(f"task:{task_id}")
    if not task_info:
        raise HTTPException(404, "Task not found")

    return {
        "task_id": task_id,
        "status": task_info.get(b"status", b"unknown").decode(),
        "created_at": task_info.get(b"created_at", b"").decode(),
    }


@app.get("/result/{task_id}", tags=["Task Management"])
async def get_task_result(task_id: str) -> Response:
    """
    Get the result of a completed upscaling task.

    Returns the upscaled image for completed tasks. Make sure to check the task status
    is "completed" before requesting the result.

    ## Error Cases:
    - 404: Task not found (invalid ID or expired)
    - 400: Task not yet completed
    - 404: Result not found (task completed but result expired)

    Results are stored for 24 hours after task completion.
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


@app.get("/jobs", response_model=JobList, tags=["Task Management"])
async def list_jobs() -> Dict[str, List[Dict[str, str]]]:
    """
    List all upscaling jobs in the system.

    Returns a list of all tasks and their current status. This is useful for:
    - Monitoring overall system usage
    - Finding specific task IDs
    - Checking task creation times

    Results are sorted by creation time (newest first).
    Only shows tasks from the last 24 hours.
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


@app.get("/health", tags=["System"])
def health_check():
    """
    Health check endpoint.

    Used for monitoring system health and uptime. Returns a simple status response.
    A 200 status code indicates the service is healthy and ready to accept requests.
    """
    return {"status": "ok"}
