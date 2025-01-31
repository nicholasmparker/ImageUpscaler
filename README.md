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

## Development Setup

### Initial Setup

1. Create a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies and set up pre-commit hooks:
   ```bash
   make install
   ```

### Development Commands

We provide several make commands to help with development:

- `make format`: Format code using Black and Ruff
- `make lint`: Run linting checks
- `make clean`: Clean up Python cache files
- `make docker-build`: Build Docker images
- `make docker-up`: Start Docker containers
- `make docker-down`: Stop Docker containers

### GitHub Workflow Status

To check the status of GitHub Actions after pushing:

1. Push and automatically check status:
   ```bash
   make push-and-check
   ```

2. Or check status manually after pushing:
   ```bash
   make check-status
   ```

The status checker will:
- Show the status of all workflow runs for your commit
- Update every 30 seconds for up to 2.5 minutes
- Use color coding to indicate success/failure/in-progress
- Provide a link to the GitHub Actions dashboard if needed

### Pre-commit Hooks

The repository is set up with pre-commit hooks that run automatically before each commit:

- Black (code formatting)
- Ruff (linting)
- YAML/TOML validation
- File checks (trailing whitespace, large files, etc.)

If a hook fails, the commit will be aborted. You can run `make format` to fix most issues automatically.

### Manual Checks

To run checks manually:

1. Format code:
   ```bash
   make format
   ```

2. Run linting:
   ```bash
   make lint
   ```

## Development

- Code formatting is handled by Black
- Security scanning is done with Snyk
- CI/CD is handled by GitHub Actions
