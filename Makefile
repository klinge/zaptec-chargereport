.PHONY: test test-cov install-dev lint clean

# Install development dependencies
install-dev:
	pip install -r requirements-dev.txt

# Run tests
test:
	pytest

# Run tests with coverage report
test-cov:
	pytest --cov=src --cov-report=html --cov-report=term

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