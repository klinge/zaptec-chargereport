#!/bin/bash
# Advanced cron health check with multiple alert methods
# Includes rate limiting to avoid spam

APP_DIR="/var/www/html/zaptec-chargereport"
LOG_FILE="$APP_DIR/data/logs/health_check.log"
FAILURE_FLAG="$APP_DIR/data/.health_check_failed"
ALERT_EMAIL="your-admin@example.com"

cd "$APP_DIR"

# Function to send alert (only once per failure)
send_alert() {
    local failure_time="$1"
    local log_content="$2"
    
    # Check if we already sent alert for this failure
    if [[ -f "$FAILURE_FLAG" ]]; then
        echo "$(date): Alert already sent, skipping" >> "$LOG_FILE"
        return
    fi
    
    # Create failure flag to prevent spam
    echo "$failure_time" > "$FAILURE_FLAG"
    
    # Method 1: Email via your existing EmailService
    python3 -c "
import sys
sys.path.append('$APP_DIR')
from src.services.email_service import EmailService
try:
    email = EmailService()
    subject = 'Zaptec Health Check FAILED'
    body = '''Zaptec health check failed at $failure_time

Last log entries:
$log_content

Please investigate the application status.'''
    email.send_error(body)
    print('Alert sent via EmailService')
except Exception as e:
    print(f'EmailService alert failed: {e}')
    # Fallback to system mail
    import subprocess
    mail_content = f'''Subject: Zaptec Health Check FAILED
To: $ALERT_EMAIL

{body}'''
    subprocess.run(['sendmail', '$ALERT_EMAIL'], input=mail_content.encode())
"
}

# Function to clear failure flag on success
clear_failure_flag() {
    if [[ -f "$FAILURE_FLAG" ]]; then
        rm "$FAILURE_FLAG"
        echo "$(date): Health restored, cleared failure flag" >> "$LOG_FILE"
        
        # Optional: Send recovery notification
        python3 -c "
import sys
sys.path.append('$APP_DIR')
from src.services.email_service import EmailService
try:
    email = EmailService()
    email.send_error('Zaptec health check RECOVERED at $(date)')
except:
    pass
"
    fi
}

# Run health check
echo "$(date): Starting health check" >> "$LOG_FILE"

source venv/bin/activate

if python smoke_tests.py >> "$LOG_FILE" 2>&1; then
    echo "$(date): Health check PASSED" >> "$LOG_FILE"
    clear_failure_flag
    exit 0
else
    echo "$(date): Health check FAILED" >> "$LOG_FILE"
    failure_time=$(date)
    log_content=$(tail -20 "$LOG_FILE")
    send_alert "$failure_time" "$log_content"
    exit 1
fi