.PHONY: test test-cov test-contracts install-dev lint autofix autofix-check clean

# Install development dependencies
install-dev:
	pip install -r requirements-dev.txt

# Run tests
test:
	pytest -m "not integration"

# Run tests with coverage report
test-cov:
	pytest --cov=src --cov-report=html --cov-report=term

# Run API contract tests
test-contracts:
	DOTENV_FILE=.env pytest tests/test_api_contract.py tests/test_api_field_mapping.py -v -m integration

# Run linting
lint:
	flake8 src/

# Preview auto-fix changes without applying
autofix-check:
	autoflake --recursive --remove-all-unused-imports --remove-unused-variables src/ tests/

# Auto-fix linting issues
autofix:
	autoflake --in-place --recursive --remove-all-unused-imports --remove-unused-variables src/ tests/
	autopep8 --in-place --recursive --aggressive --aggressive src/ tests/
	black src/ tests/

# Clean up test artifacts
clean:
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete