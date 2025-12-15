#!/usr/bin/env python3
"""
Example monitoring integration for production deployments.
Customize webhook URLs and notification methods for your setup.
"""
import requests
import json
from datetime import datetime

def send_deployment_notification(success: bool, details: str = ""):
    """Send deployment status to monitoring system"""
    
    # Example webhook URLs (replace with your actual monitoring system)
    SLACK_WEBHOOK = "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
    TEAMS_WEBHOOK = "https://your-org.webhook.office.com/webhookb2/YOUR-TEAMS-WEBHOOK"
    
    status = "✅ SUCCESS" if success else "❌ FAILED"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    message = {
        "text": f"Zaptec Deployment {status}",
        "attachments": [{
            "color": "good" if success else "danger",
            "fields": [
                {"title": "Service", "value": "Zaptec Charge Report", "short": True},
                {"title": "Status", "value": status, "short": True},
                {"title": "Time", "value": timestamp, "short": True},
                {"title": "Details", "value": details or "No additional details", "short": False}
            ]
        }]
    }
    
    # Uncomment and configure for your monitoring system:
    
    # # Slack notification
    # try:
    #     response = requests.post(SLACK_WEBHOOK, json=message, timeout=10)
    #     response.raise_for_status()
    # except Exception as e:
    #     print(f"Failed to send Slack notification: {e}")
    
    # # Email notification (using your existing EmailService)
    # try:
    #     from src.services.email_service import EmailService
    #     email_service = EmailService()
    #     subject = f"Zaptec Deployment {status}"
    #     body = f"Deployment completed at {timestamp}\nStatus: {status}\nDetails: {details}"
    #     email_service.send_error(body)  # Reuse error email for notifications
    # except Exception as e:
    #     print(f"Failed to send email notification: {e}")
    
    print(f"Deployment notification: {status} at {timestamp}")

def check_application_health():
    """Additional health checks you might want to run periodically"""
    
    # Example: Check if log files are being created
    # Example: Verify last successful report generation
    # Example: Check disk space for report storage
    
    return True

if __name__ == "__main__":
    # Example usage
    send_deployment_notification(True, "All smoke tests passed successfully")