.PHONY: install format lint test clean check-status

install:
	pre-commit install

format:
	black .
	ruff check --fix .

lint:
	black . --check
	ruff check .

test-e2e: ## Run end-to-end tests
	@if [ -z "$(IMAGE)" ]; then \
		echo "Error: Please provide an image path using IMAGE=path/to/image.jpg"; \
		exit 1; \
	fi
	./tests/e2e/run_test.sh "$(IMAGE)"

test: 
	# Add test command here

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +

# GitHub commands
check-status:
	./scripts/check_github_status.sh

push-and-check: ## Push to GitHub and check workflow status
	git push && make check-status

# Docker commands
docker-build:
	docker compose build

docker-up:
	docker compose up

docker-down:
	docker compose down
