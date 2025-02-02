import os
from typing import Dict, List
import asyncio

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import Response
from redis.asyncio import Redis
import httpx

from app.tasks import process_image

app = FastAPI()

# Simple Redis connection
redis = Redis(
    host=os.environ.get("REDIS_HOST", "redis"),
    port=int(os.environ.get("REDIS_PORT", "6379")),
    password=os.environ.get("REDIS_PASSWORD", ""),
    decode_responses=False  # Keep binary data for image results
)

@app.post("/upscale")
async def upscale_image_sync(image: UploadFile) -> Response:
    """Synchronously upscale an image"""
    if not image:
        raise HTTPException(400, "No file uploaded")

    try:
        # Read image data
        image_data = await image.read()
        
        # Send to ESRGAN service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://esrgan:8001/upscale",
                content=image_data,
                headers={"Content-Type": image.content_type or "image/jpeg"},
                timeout=float(os.getenv("REQUEST_TIMEOUT", "300"))
            )
            response.raise_for_status()
            return Response(content=response.content, media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/upscale/async")
async def upscale_image_async(image: UploadFile) -> Dict[str, str]:
    """Asynchronously upscale an image"""
    if not image:
        raise HTTPException(400, "No file uploaded")

    try:
        # Process image and get task ID
        task_id = await process_image(image, redis)
        return {"task_id": task_id}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/status/{task_id}")
async def get_task_status(task_id: str) -> Dict[str, str]:
    """Get the status of a task"""
    task_info = await redis.hgetall(f"task:{task_id}")
    if not task_info:
        raise HTTPException(404, "Task not found")

    return {
        "task_id": task_id,
        "status": task_info.get(b"status", b"unknown").decode(),
        "created_at": task_info.get(b"created_at", b"").decode()
    }

@app.get("/result/{task_id}")
async def get_task_result(task_id: str) -> Response:
    """Get the result of a completed task"""
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

@app.get("/jobs")
async def list_jobs() -> Dict[str, List[Dict[str, str]]]:
    """List all jobs"""
    jobs = []
    async for key in redis.scan_iter("task:*"):
        task_id = key.decode().split(":", 1)[1]
        task_info = await redis.hgetall(key)
        jobs.append({
            "task_id": task_id,
            "status": task_info.get(b"status", b"unknown").decode(),
            "created_at": task_info.get(b"created_at", b"").decode()
        })
    return {"jobs": jobs}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok"}
