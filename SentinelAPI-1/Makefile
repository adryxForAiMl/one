# Makefile for SentinelAPI: Zero-Trust API Vulnerability Scanner

# Define variables
PYTHON = python3
PIP = pip
FLAKE8 = flake8
TEST = pytest
DOCKER = docker
DOCKER_COMPOSE = docker-compose

# Define targets
.PHONY: install lint test run build

# Install dependencies
install:
	$(PIP) install -r requirements.txt

# Lint the code
lint:
	$(FLAKE8) app tests

# Run tests
test:
	$(TEST)

# Run the application
run:
	$(PYTHON) -m app.main

# Build Docker images
build:
	$(DOCKER_COMPOSE) build

# Run Docker containers
up:
	$(DOCKER_COMPOSE) up

# Stop Docker containers
down:
	$(DOCKER_COMPOSE) down

# Clean up Docker images and containers
clean:
	$(DOCKER) system prune -f
