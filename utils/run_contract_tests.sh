#!/bin/bash
# Run API contract tests to verify Zaptec API hasn't changed
# These tests make REAL API calls

set -e

echo "🔍 Running Zaptec API contract tests..."

cd /var/www/html/zaptec-chargereport
source venv/bin/activate

# Run all API contract and field mapping tests with production environment
DOTENV_FILE=.env python -m pytest tests/test_api_contract.py tests/test_api_field_mapping.py -v -m integration --override-ini="env_files=.env"

if [ $? -eq 0 ]; then
    echo "✅ API contract tests passed - Zaptec API is working as expected"
else
    echo "❌ API contract tests failed - Zaptec API may have changed!"
    echo "Check the test output for details about what changed."
    exit 1
fi