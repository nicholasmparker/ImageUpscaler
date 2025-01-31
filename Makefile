.PHONY: install format lint test clean check-status

install:
	pip install -r requirements.txt
	pre-commit install

format:
	black .
	ruff check --fix .

lint:
	black . --check
	ruff check .

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
	docker-compose build

docker-up:
	docker-compose up

docker-down:
	docker-compose down
