# Running Tests

This project uses end-to-end tests to verify the functionality of the image upscaling service. The tests are containerized and run using Docker Compose.

## Running the Tests

To run the tests, simply use:

```bash
docker compose -f docker-compose.dev.yml run test
```

This will:
1. Start the API and ESRGAN services if they're not already running
2. Wait for both services to be healthy
3. Run the end-to-end tests in a dedicated test container
4. Display the test results with verbose output

## Test Structure

The tests are located in `tests/e2e/test_upscale.py` and verify:
- Synchronous image upscaling
- Asynchronous image upscaling
- Task status checking
- Error handling

## Test Environment

The test container is configured with:
- `API_HOST` and `API_PORT` environment variables pointing to the API service
- All necessary test dependencies from `requirements/test.txt`
- Volume mounting of the project directory for live code updates
