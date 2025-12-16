.PHONY: local test lint format prod clean help install dev migrate
.PHONY: infra-init infra-plan infra-apply infra-destroy k8s-deploy k8s-logs k8s-status

# Default target
help:
	@echo "Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  make install    - Install dependencies"
	@echo "  make dev        - Install dev dependencies"
	@echo "  make local      - Start local development server"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linting and type checking"
	@echo "  make format     - Format code"
	@echo "  make migrate    - Run database migrations"
	@echo "  make clean      - Clean up generated files"
	@echo ""
	@echo "Docker:"
	@echo "  make prod       - Start production with Docker Compose"
	@echo "  make prod-down  - Stop production"
	@echo "  make prod-logs  - View production logs"
	@echo ""
	@echo "Load Testing:"
	@echo "  make loadtest-install - Install Locust dependencies"
	@echo "  make loadtest-smoke   - Smoke test (1 user, 30s)"
	@echo "  make loadtest-load    - Load test (50 users, 5m)"
	@echo "  make loadtest-stress  - Stress test (200 users, 10m)"
	@echo "  make loadtest-spike   - Spike test (100 users, 5m)"
	@echo "  make loadtest-ui      - Interactive Locust UI"
	@echo "  make loadtest-docker  - Distributed testing with Docker"
	@echo ""
	@echo "Infrastructure (Hetzner + k3s):"
	@echo "  make infra-init    - Initialize Terraform"
	@echo "  make infra-plan    - Plan infrastructure changes"
	@echo "  make infra-apply   - Deploy full infrastructure"
	@echo "  make infra-destroy - Tear down infrastructure"
	@echo ""
	@echo "Kubernetes:"
	@echo "  make k8s-deploy - Deploy/update application"
	@echo "  make k8s-logs   - View application logs"
	@echo "  make k8s-status - Check cluster status"

# Install production dependencies
install:
	uv sync --no-dev

# Install all dependencies including dev
dev:
	uv sync

# Run database migrations
migrate:
	uv run alembic upgrade head

# Local development
local: dev migrate
	uv run uvicorn qna_agent.main:app --host 0.0.0.0 --port 8000 --reload

# Run tests
test:
	uv run pytest -v --tb=short

# Run tests with coverage
test-cov:
	uv run pytest -v --tb=short --cov=src/qna_agent --cov-report=term-missing

# Lint and type check
lint:
	uv run ruff check .
	uv run basedpyright

# Security scan
security:
	uv run bandit -r src/

# Format code
format:
	uv run ruff format .
	uv run ruff check . --fix

# Production with Docker Compose
prod:
	docker compose -f docker-compose.prod.yml up -d --build

# Stop production
prod-down:
	docker compose -f docker-compose.prod.yml down

# View production logs
prod-logs:
	docker compose -f docker-compose.prod.yml logs -f

# Local Docker development
docker-local:
	docker compose up -d --build

# Stop local Docker
docker-local-down:
	docker compose down

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov/ dist/ build/ *.egg-info/
	rm -rf data/*.db

# =============================================================================
# Infrastructure (Hetzner Cloud + k3s)
# =============================================================================

# Initialize Terraform
infra-init:
	terraform -chdir=terraform init

# Plan infrastructure changes
infra-plan:
	@echo "Required env vars: HCLOUD_TOKEN, DB_PASSWORD, LITELLM_API_KEY"
	terraform -chdir=terraform plan

# Deploy full infrastructure (setup script)
infra-apply:
	./scripts/setup.sh

# Tear down infrastructure
infra-destroy:
	./scripts/teardown.sh

# Force destroy (no confirmation)
infra-destroy-force:
	./scripts/teardown.sh --force

# =============================================================================
# Kubernetes Operations
# =============================================================================

# Deploy/update application only
k8s-deploy:
	./scripts/deploy-app.sh

# View application logs
k8s-logs:
	kubectl -n qna-agent logs -f -l app=qna-agent --all-containers

# Check cluster status
k8s-status:
	@echo "=== Nodes ==="
	kubectl get nodes
	@echo ""
	@echo "=== Pods ==="
	kubectl -n qna-agent get pods -o wide
	@echo ""
	@echo "=== Services ==="
	kubectl -n qna-agent get svc
	@echo ""
	@echo "=== Deployments ==="
	kubectl -n qna-agent get deployments

# Get shell into application pod
k8s-shell:
	kubectl -n qna-agent exec -it deployment/qna-agent -- /bin/sh

# Restart deployment
k8s-restart:
	kubectl -n qna-agent rollout restart deployment/qna-agent

# View pod events
k8s-events:
	kubectl -n qna-agent get events --sort-by='.lastTimestamp'

# =============================================================================
# Load Testing
# =============================================================================

.PHONY: loadtest-install loadtest-smoke loadtest-load loadtest-stress loadtest-spike
.PHONY: loadtest-ui loadtest-docker loadtest-docker-down loadtest-setup

# Install load test dependencies
loadtest-install:
	uv sync --extra loadtest

# Create reports directory
loadtest-setup:
	mkdir -p reports

# Run smoke test (single user, verify endpoints)
loadtest-smoke: loadtest-setup
	uv run locust -f loadtests/scenarios/smoke.py \
		--host=http://localhost:8000 \
		--users=1 \
		--spawn-rate=1 \
		--run-time=30s \
		--headless \
		--html=reports/smoke_test.html

# Run load test (normal expected load)
loadtest-load: loadtest-setup
	uv run locust -f loadtests/locustfile.py \
		--host=http://localhost:8000 \
		--users=50 \
		--spawn-rate=5 \
		--run-time=5m \
		--headless \
		--html=reports/load_test.html

# Run stress test (push beyond normal capacity)
loadtest-stress: loadtest-setup
	uv run locust -f loadtests/locustfile.py \
		--host=http://localhost:8000 \
		--users=200 \
		--spawn-rate=20 \
		--run-time=10m \
		--headless \
		--html=reports/stress_test.html

# Run spike test (sudden traffic bursts)
loadtest-spike: loadtest-setup
	uv run locust -f loadtests/locustfile.py \
		--host=http://localhost:8000 \
		--users=100 \
		--spawn-rate=50 \
		--run-time=5m \
		--headless \
		--html=reports/spike_test.html

# Interactive Locust UI (for manual testing)
loadtest-ui:
	uv run locust -f loadtests/locustfile.py \
		--host=http://localhost:8000

# Start distributed load testing with Docker
loadtest-docker:
	docker compose -f loadtests/docker-compose.loadtest.yml up -d --build
	@echo ""
	@echo "Load testing environment started!"
	@echo "  - Locust UI: http://localhost:8089"
	@echo "  - App: http://localhost:8000"
	@echo "  - Mock LLM: http://localhost:8001"
	@echo ""

# Stop distributed load testing
loadtest-docker-down:
	docker compose -f loadtests/docker-compose.loadtest.yml down

# View load test logs
loadtest-docker-logs:
	docker compose -f loadtests/docker-compose.loadtest.yml logs -f
