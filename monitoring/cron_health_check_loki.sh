#!/bin/bash
# Health check with structured logging for Loki/Grafana
# Outputs JSON logs that Promtail can easily parse

APP_DIR="/var/www/html/zaptec-chargereport"
LOG_FILE="$APP_DIR/data/logs/health_check_structured.log"

cd "$APP_DIR"

# Function to log structured JSON for Loki
log_structured() {
    local level="$1"
    local message="$2"
    local status="$3"
    local details="$4"
    
    jq -n \
        --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)" \
        --arg level "$level" \
        --arg service "zaptec-health-check" \
        --arg message "$message" \
        --arg status "$status" \
        --arg details "$details" \
        --arg host "$(hostname)" \
        '{
            timestamp: $timestamp,
            level: $level,
            service: $service,
            message: $message,
            status: $status,
            details: $details,
            host: $host
        }' >> "$LOG_FILE"
}

# Start health check
log_structured "INFO" "Starting health check" "running" ""

source venv/bin/activate

# Capture smoke test output
if smoke_output=$(python smoke_tests.py 2>&1); then
    log_structured "INFO" "Health check completed successfully" "healthy" "All tests passed"
    exit 0
else
    # Extract failure details from smoke test output
    failure_details=$(echo "$smoke_output" | grep -E "(ERROR|FAILED)" | tail -5 | tr '\n' ' ')
    
    log_structured "ERROR" "Health check failed" "unhealthy" "$failure_details"
    
    # Also log individual test failures for better alerting
    echo "$smoke_output" | grep -E "ERROR.*:" | while read -r error_line; do
        test_name=$(echo "$error_line" | sed 's/.*Testing \([^.]*\).*/\1/' | tr ' ' '_')
        error_msg=$(echo "$error_line" | sed 's/.*ERROR - //')
        log_structured "ERROR" "Test failed: $test_name" "test_failed" "$error_msg"
    done
    
    exit 1
fi