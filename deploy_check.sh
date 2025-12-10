#!/bin/bash
# Post-deployment smoke test script
# Usage: ./deploy_check.sh

set -e

echo "🚀 Starting post-deployment checks..."

# Activate virtual environment
source venv/bin/activate

# Run smoke tests
echo "📋 Running smoke tests..."
python smoke_tests.py

if [ $? -eq 0 ]; then
    echo "✅ All smoke tests passed - deployment successful!"
    
    # Optional: Send success notification
    # curl -X POST "your-monitoring-webhook" -d "Zaptec deployment successful"
    
    exit 0
else
    echo "❌ Smoke tests failed - deployment issues detected!"
    
    # Optional: Send failure notification
    # curl -X POST "your-monitoring-webhook" -d "Zaptec deployment failed smoke tests"
    
    exit 1
fi