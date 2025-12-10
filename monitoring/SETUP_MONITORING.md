# Monitoring Setup Guide

## Option 1: Simple Email Alerts

### Setup
```bash
# Make scripts executable
chmod +x cron_health_check.sh

# Edit the script to set your email
nano cron_health_check.sh
# Change: ALERT_EMAIL="your-admin@example.com"

# Add to crontab
crontab -e
# Add: 0 */6 * * * /var/www/html/zaptec-chargereport/cron_health_check.sh
```

### Requirements
- System `sendmail` configured
- Or use the advanced script that uses your EmailService

## Option 2: Advanced Monitoring (Recommended)

### Features
- **Rate limiting**: Only sends one alert per failure (no spam)
- **Recovery notifications**: Alerts when service recovers
- **Multiple alert methods**: Uses your EmailService + fallback
- **Detailed logging**: Includes last 20 log lines in alerts

### Setup
```bash
chmod +x cron_health_check_advanced.sh

# Edit email address
nano cron_health_check_advanced.sh

# Add to crontab (every 6 hours)
crontab -e
0 */6 * * * /var/www/html/zaptec-chargereport/cron_health_check_advanced.sh

# Or more frequent (every 2 hours)
0 */2 * * * /var/www/html/zaptec-chargereport/cron_health_check_advanced.sh
```

## Option 3: External Monitoring Service

### Using a service like UptimeRobot, Pingdom, or StatusCake:

1. Create a simple HTTP endpoint:
```python
# health_endpoint.py
from flask import Flask, jsonify
import subprocess
import os

app = Flask(__name__)

@app.route('/health')
def health_check():
    try:
        result = subprocess.run([
            '/var/www/html/zaptec-chargereport/venv/bin/python',
            '/var/www/html/zaptec-chargereport/smoke_tests.py'
        ], capture_output=True, timeout=30)
        
        if result.returncode == 0:
            return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})
        else:
            return jsonify({"status": "unhealthy", "error": result.stderr.decode()}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

2. Configure external service to monitor `http://your-server:8080/health`

## Option 4: Slack/Teams Integration

Add to your health check script:
```bash
# Slack webhook notification
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Zaptec health check failed at $(date)"}' \
  YOUR_SLACK_WEBHOOK_URL
```

## Recommended Cron Schedule

```bash
# Every 6 hours (good for production)
0 */6 * * * /path/to/cron_health_check_advanced.sh

# Every 2 hours (if you want faster detection)
0 */2 * * * /path/to/cron_health_check_advanced.sh

# Daily at 8 AM (minimal monitoring)
0 8 * * * /path/to/cron_health_check.sh
```

## Log Management

Health check logs will accumulate over time. Add log rotation:

```bash
# Add to crontab to clean old logs (keep last 30 days)
0 2 * * * find /var/www/html/zaptec-chargereport/data/logs -name "health_check.log" -mtime +30 -delete
```