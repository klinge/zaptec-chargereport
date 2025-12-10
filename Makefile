.PHONY: test test-cov test-contracts install-dev lint clean

# Install development dependencies
install-dev:
	pip install -r requirements-dev.txt

# Run tests
test:
	pytest

# Run tests with coverage report
test-cov:
	pytest --cov=src --cov-report=html --cov-report=term

# Run API contract tests
test-contracts:
	DOTENV_FILE=.env pytest tests/test_api_contract.py tests/test_api_field_mapping.py -v -m integration

# Run linting
lint:
	flake8 src/ tests/

# Clean up test artifacts
clean:
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete