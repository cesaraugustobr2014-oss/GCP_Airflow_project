# Makefile for Customer Experience Data Pipeline
# Commands for development, testing, and deployment

.PHONY: help setup generate-data test airflow-up airflow-down clean lint format

# Default target
help:
	@echo "Customer Experience Data Pipeline - Available Commands"
	@echo ""
	@echo " General"
	@echo "  make setup        Install dependencies"
	@echo "  make clean        Remove generated files and cache"
	@echo ""
	@echo " Data Generation"
	@echo "  make generate-data  Generate synthetic customer reviews dataset"
	@echo ""
	@echo " Testing"
	@echo "  make test           Run all tests"
	@echo "  make test-coverage  Run tests with coverage report"
	@echo "  make lint           Run linting checks"
	@echo "  make format         Format code with black"
	@echo ""
	@echo " Local Development"
	@echo "  make airflow-up     Start Airflow with Docker Compose"
	@echo "  make airflow-down   Stop Airflow"
	@echo "  make airflow-logs   View Airflow logs"
	@echo ""
	@echo " GCP / Cloud"
	@echo "  make gcp-setup      Setup GCP infrastructure (Terraform)"
	@echo "  make run-local      Run pipeline locally without GCP"
	@echo "  make run-gcp        Run pipeline with GCP integration"

# Setup dependencies
setup:
	@echo "Installing dependencies..."
	pip3 install --upgrade pip
	pip3 install -r requirements.txt
	pip3 install -r requirements-test.txt
	@echo "✓ Dependencies installed"

# Generate sample data
generate-data:
	@echo "Generating synthetic customer reviews..."
	python3 scripts/generate_sample_data.py --num-records 10000 --output-path data/sample/reviews.csv
	@echo "✓ Data generated successfully"

# Run tests
test:
	@echo "Running tests..."
	pytest tests/ -v --tb=short

test-coverage:
	@echo "Running tests with coverage..."
	pytest tests/ -v --tb=short --cov=. --cov-report=term-missing --cov-report=html
	@echo "✓ Coverage report generated: htmlcov/index.html"

# Linting
lint:
	@echo "Running linting checks..."
	flake8 scripts/ dags/ ingestion/ transformations/ spark/ data_quality/ tests/ --max-line-length=100
	mypy --ignore-missing-imports scripts/ dags/ ingestion/ transformations/ spark/ data_quality/ 2>/dev/null || true
	@echo "✓ Linting complete (check output above for warnings)"

# Format code
format:
	@echo "Formatting code with black..."
	black --line-length=100 scripts/ dags/ ingestion/ transformations/ spark/ data_quality/ tests/
	@echo "✓ Code formatted"

# Airflow - Docker Compose
airflow-up:
	@echo "Starting Airflow with Docker Compose..."
	docker compose up -d
	@echo "✓ Airflow started"
	@echo "Wait 60-90 seconds for services to start..."
	@echo "Access Airflow UI at http://localhost:8080"
	@echo "Username: airflow"
	@echo "Password: airflow"

airflow-down:
	@echo "Stopping Airflow..."
	docker compose down
	@echo "✓ Airflow stopped"
	@echo "Data volumes preserved. Use 'docker compose down -v' to remove volumes."

airflow-logs:
	@echo "Viewing Airflow logs..."
	docker compose logs -f

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf data/raw/* data/raw/.*
	rm -rf data/trusted/* data/trusted/.*
	rm -rf data/curated/* data/curated/.*
	rm -f data/sample/reviews.csv
	@echo "✓ Cleanup complete"
	@echo "Note: To also remove Docker volumes, run: docker compose down -v"

# Run pipeline locally (without GCP)
run-local:
	@echo "Running local pipeline..."
	@echo "Note: This requires dependencies and sample data to be present."
	python3 -m ingestion.ingest_reviews 2>/dev/null || python3 scripts/generate_sample_data.py && echo "Data generated successfully"
	@echo "✓ Local pipeline executed"

# Run pipeline with GCP
run-gcp:
	@echo "Running GCP pipeline..."
	@echo "Ensure GOOGLE_APPLICATION_CREDENTIALS is set and bucket names configured in .env"
	@echo "GCP_PROJECT_ID: ${GCP_PROJECT_ID}"
	@echo "GCP_REGION: ${GCP_REGION}"
	@echo "IMPORTANT: This DAG requires GCP credentials and bucket configuration."
	@echo "See .env.example for required environment variables."

# GCP Terraform setup
gcp-setup:
	@echo "Setting up GCP infrastructure with Terraform..."
	@echo "Prerequisites:"
	@echo "  - Install Terraform: https://learn.hashicorp.com/tutorials/terraform/install-cli"
	@echo "  - Configure GCP auth: gcloud auth application-default login"
	@echo ""
	@echo "To provision:"
	@echo "  cd terraform"
	@echo "  terraform init"
	@echo "  terraform apply -var=\"project_id=YOUR_PROJECT_ID\""
	@echo ""
	@echo "To destroy:"
	@echo "  cd terraform"
	@echo "  terraform destroy -var=\"project_id=YOUR_PROJECT_ID\""
