# Image Upscaler API

A simple REST API that upscales images using Real-ESRGAN and delivers results via webhook.

## Features

- Upload images for upscaling using Real-ESRGAN
- Supports both CPU and GPU processing
- Asynchronous processing with Redis queue
- Webhook delivery of processed images
- Docker-based deployment
- CI/CD with GitHub Actions

## Quick Start

1. Make sure you have Docker and Docker Compose installed
2. Clone this repository
3. Choose your processing mode:

   **CPU Mode (Default):**
   ```bash
   docker-compose up --build
   ```

   **GPU Mode (Requires NVIDIA Docker):**
   ```bash
   # Make sure you have nvidia-docker2 installed
   USE_GPU=1 docker-compose up --build
   ```

## Hardware Requirements

### CPU Mode
- No special requirements
- Slower processing
- Uses more memory due to tiling

### GPU Mode
- Requires NVIDIA GPU
- Requires nvidia-docker2 installed
- Significantly faster processing
- More efficient memory usage

## API Usage

Upload an image for processing:
```bash
curl -X POST "http://localhost:8000/upscale" \
  -F "image=@your_image.jpg" \
  -F "webhook_url=http://your-webhook-url.com/callback"
```

The API will return a task ID that you can use to track the progress:
```json
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "processing"
}
```

## Health Check

You can check the current processing mode (CPU/GPU) using:
```bash
curl "http://localhost:8001/health"
```

Response will include the current device being used:
```json
{
  "status": "healthy",
  "device": "cuda",  # or "cpu"
  "gpu_available": true  # or false
}
```

## Development

- Code formatting is handled by Black
- Security scanning is done with Snyk
- CI/CD is handled by GitHub Actions
