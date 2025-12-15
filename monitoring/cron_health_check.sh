#!/bin/bash
# Cron-friendly health check with alerting
# Usage in crontab: 0 */6 * * * /var/www/html/zaptec-chargereport/cron_health_check.sh

set -e

APP_DIR="/var/www/html/zaptec-chargereport"
LOG_FILE="$APP_DIR/data/logs/health_check.log"
ALERT_EMAIL="your-admin@example.com"

cd "$APP_DIR"

# Create log entry
echo "$(date): Starting health check" >> "$LOG_FILE"

# Activate venv and run smoke tests
source venv/bin/activate

if python smoke_tests.py >> "$LOG_FILE" 2>&1; then
    echo "$(date): Health check PASSED" >> "$LOG_FILE"
    exit 0
else
    echo "$(date): Health check FAILED" >> "$LOG_FILE"
    
    # Send alert email using system mail
    {
        echo "Subject: Zaptec Health Check FAILED"
        echo "To: $ALERT_EMAIL"
        echo ""
        echo "Zaptec application health check failed at $(date)"
        echo ""
        echo "Last 20 lines from health check log:"
        tail -20 "$LOG_FILE"
    } | sendmail "$ALERT_EMAIL"
    
    exit 1
fi