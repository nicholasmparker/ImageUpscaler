# Image Upscaler API

A simple, Docker-based REST API that upscales images using Real-ESRGAN. Built for home use with simplicity in mind.

## Features

- Simple REST API for image upscaling
- Everything runs in Docker - no host dependencies needed
- Supports both CPU and GPU processing
- Asynchronous processing with Redis queue
- End-to-end functional testing
- Follows REST best practices

## Quick Start

1. Make sure you have Docker and Docker Compose installed
2. Clone this repository
3. Choose your processing mode:

   **CPU Mode (Default):**
   ```bash
   docker compose up --build
   ```

   **GPU Mode (Requires NVIDIA Docker):**
   ```bash
   # Make sure you have nvidia-docker2 installed
   USE_GPU=1 docker compose up --build
   ```

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

## Environment Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your configuration:
   ```
   # Redis configuration
   REDIS_HOST=redis
   REDIS_PORT=6379
   REDIS_PASSWORD=your_secure_password_here

   # ESRGAN service configuration
   REQUEST_TIMEOUT=300
   ```

3. Start the services:
   ```bash
   docker compose up
   ```

## Testing

We focus on end-to-end functional tests to ensure the application works as expected. Run the tests with:

```bash
docker compose run --rm api pytest
```

The tests verify:
- Image upload and processing
- Webhook delivery
- Error handling
- API compliance with REST best practices

## Development

### Local Development

Everything runs in Docker to ensure consistency:

1. Make your changes
2. Rebuild and run the services:
   ```bash
   docker compose up --build
   ```
3. Run the tests:
   ```bash
   docker compose run --rm api pytest
   ```

### CI/CD Pipeline

The project uses a simple GitHub Actions pipeline that:

1. Builds and tests the services in Docker
2. Uses aggressive disk cleanup for large model files
3. Pushes images to GitHub Container Registry on main branch

### Pre-commit Hooks

Basic code quality checks run before each commit:

```bash
pip install pre-commit
pre-commit install
```

## Troubleshooting

### Common Issues

1. **Out of Memory**
   - For CPU mode: Reduce `TILE_SIZE` in `.env`
   - For GPU mode: Use a GPU with more VRAM

2. **Slow Processing**
   - Enable GPU mode if available
   - Adjust worker count in `.env`

3. **Build Failures**
   - Ensure sufficient disk space (at least 10GB free)
   - Try cleaning Docker: `docker system prune -af`

### Getting Help

- Open an issue for bugs
- Use discussions for questions
- Check closed issues for solutions

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) for the upscaling model
- [FastAPI](https://fastapi.tiangolo.com/) for the API framework
