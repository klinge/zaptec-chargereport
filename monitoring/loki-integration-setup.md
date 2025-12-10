# Grafana + Loki + Promtail Integration

## Setup Steps

### 1. Update Health Check Script
```bash
# Make the Loki-compatible health check executable
chmod +x cron_health_check_loki.sh

# Install jq if not present (needed for JSON logging)
sudo apt install jq

# Update crontab to use the new script
crontab -e
# Change to: 0 */6 * * * /var/www/html/zaptec-chargereport/cron_health_check_loki.sh
```

### 2. Configure Promtail
```bash
# Copy the Promtail config to your Promtail directory
sudo cp promtail-zaptec.yml /etc/promtail/conf.d/

# Or merge with your existing promtail config
# Update the Loki URL in the config if needed

# Restart Promtail
sudo systemctl restart promtail
```

### 3. Import Grafana Dashboard
1. Open Grafana UI
2. Go to Dashboards → Import
3. Upload `grafana-dashboard.json`
4. Configure data source (your Loki instance)

### 4. Setup Grafana Alerts
1. Go to Alerting → Alert Rules
2. Import rules from `grafana-alerts.yml`
3. Configure notification channels (email, Slack, etc.)

## Log Structure

The health check now outputs structured JSON logs:
```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "level": "ERROR",
  "service": "zaptec-health-check", 
  "message": "Health check failed",
  "status": "unhealthy",
  "details": "Zaptec API connection failed: 401 Unauthorized",
  "host": "your-server"
}
```

## Useful Loki Queries

### Recent health status:
```
{service="zaptec-health-check"} | json
```

### Failed health checks:
```
{service="zaptec-health-check", status="unhealthy"}
```

### Application errors:
```
{job="zaptec-app"} |= "ERROR"
```

### API connection issues:
```
{service="zaptec-health-check"} |= "API connection failed"
```

## Dashboard Features

- **Health Status Panel**: Current health (healthy/unhealthy)
- **Recent Logs**: Last health check results
- **Error Timeline**: Application errors over time
- **Health Timeline**: Health check success/failure trends

## Alerting Rules

- **Critical**: Health check failed
- **Critical**: API connection failed  
- **Warning**: No health checks in 8 hours
- **Warning**: High error rate (>5 errors/hour)

## Benefits

✅ **Centralized monitoring** - All logs in one place  
✅ **Visual dashboards** - Easy to spot trends  
✅ **Automated alerts** - Get notified of issues  
✅ **Historical data** - Track health over time  
✅ **Structured logs** - Easy to query and filter  

## Integration with Existing Logs

Your application logs will also be ingested:
- Report generation logs
- API call logs  
- Email sending logs
- Error logs

All searchable and alertable through Grafana!