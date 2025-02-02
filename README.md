# Image Upscaler API

A simple REST API that upscales images using Real-ESRGAN and delivers results via webhook.

## Features

- Upload images for upscaling using Real-ESRGAN
- Supports both CPU and GPU processing
- Asynchronous processing with Redis queue
- Webhook delivery of processed images
- Docker-based deployment
- CI/CD with GitHub Actions
- End-to-end testing

## Example Results

| Before (Original) | After (4x Upscaled) |
|:----------------:|:-------------------:|
| ![Before](docs/images/example_before.jpg) | ![After](docs/images/example_after.jpg) |

*Note: The example above shows 4x upscaling using the RealESRGAN_x4plus model. Results may vary depending on the input image quality and content.*

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

For information about running tests, see the [Test Documentation](tests/README.md).

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

### Code Quality

The project uses several tools to maintain code quality:

1. **Black** - Code formatting
   - Configured in `pyproject.toml`
   - Run automatically in pre-commit and CI

2. **Ruff** - Fast Python linter
   - Run automatically in pre-commit and CI
   - Helps catch common issues

3. **Snyk** - Security vulnerability scanning
   - Scans production dependencies
   - Runs on every push and PR
   - Configured to check for high-severity issues

### Pre-commit Hooks

Install pre-commit hooks to ensure code quality before committing:

```bash
pip install pre-commit
pre-commit install
```

This will automatically:
- Format code with Black
- Run Ruff linting
- Check for sensitive data
- Ensure consistent file formatting

## Deploying with Portainer

This application can be easily deployed using Portainer. Follow these steps:

1. Log into your Portainer instance
2. Go to "Stacks" in the left sidebar
3. Click "Add stack"
4. Name your stack (e.g., "image-upscaler")
5. Under "Build method", select "Upload"
6. Upload the `portainer-stack.yml` file from this repository
7. Click "Deploy the stack"

The stack will create:
- An initialization container to download the ESRGAN model
- The API service running on port 8000
- The ESRGAN service running on port 8001

### Important Notes

- The stack uses a named volume (`esrgan_models`) to persist the downloaded model file
- Both services have health checks configured
- The ESRGAN service will wait for the model to be downloaded before starting
- The services are configured to restart automatically unless stopped manually

### Testing the Deployment

After deployment, you can test the service by:

1. Visit `http://<your-host>:8000/docs` to view the API documentation
2. Use the `/upscale/sync` endpoint to test image upscaling
3. Monitor the service logs in Portainer for any issues

## Development

- Code formatting is handled by Black
- Security scanning is done with Snyk
- CI/CD is handled by GitHub Actions
