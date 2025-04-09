.PHONY: help up down build test lint clean logs

# Default target
help:
	@echo "FinTech Data Platform - Available Commands:"
	@echo "  make up      - Start all services with docker-compose"
	@echo "  make down    - Stop all services"
	@echo "  make build   - Build Docker images"
	@echo "  make test    - Run tests"
	@echo "  make lint    - Run linting"
	@echo "  make clean   - Clean up containers and volumes"
	@echo "  make logs    - Show logs from all services"

# Start all services
up:
	@echo "Starting FinTech Data Platform..."
	docker-compose up -d
	@echo "Services started! Access:"
	@echo "  API: http://localhost:8000"
	@echo "  Dashboard: http://localhost:8061"
	@echo "  Grafana: http://localhost:3000 (admin/admin)"
	@echo "  Prometheus: http://localhost:9090"

# Stop all services
down:
	@echo "Stopping FinTech Data Platform..."
	docker-compose down

# Build Docker images
build:
	@echo "Building Docker images..."
	docker-compose build

# Run tests
test:
	@echo "Running tests..."
	pytest tests/ -v

# Run linting
lint:
	@echo "Running linting..."
	black app/ tests/
	flake8 app/ tests/

# Clean up
clean:
	@echo "Cleaning up..."
	docker-compose down -v
	docker system prune -f

# Show logs
logs:
	docker-compose logs -f

# Development helpers
dev-setup:
	@echo "Setting up development environment..."
	pip install -r requirements.txt
	cp env.example .env
	@echo "Development environment ready!"

# Database migrations
migrate:
	@echo "Running database migrations..."
	alembic upgrade head

# Create migration
migration:
	@echo "Creating new migration..."
	alembic revision --autogenerate -m "$(message)"

# Load test
load-test:
	@echo "Running load test..."
	locust -f tests/load_test.py --host=http://localhost:8000
