#!/usr/bin/env python3

"""
FlipSync Alerting and Notification System
=========================================
Comprehensive alerting system with multiple notification channels
"""

import json
import logging
import os
import smtplib
import time
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Dict, List, Optional
import requests

# Configuration
ALERT_CONFIG = {
    'thresholds': {
        'cpu_percent': 80,
        'memory_percent': 85,
        'disk_percent': 90,
        'response_time_ms': 5000,
        'error_rate_percent': 5,
        'connection_count': 100
    },
    'notification_channels': {
        'email': {
            'enabled': True,
            'smtp_server': 'localhost',
            'smtp_port': 587,
            'from_email': 'alerts@flipsyncai.com',
            'to_emails': ['admin@flipsyncai.com'],
            'username': '',
            'password': ''
        },
        'slack': {
            'enabled': False,
            'webhook_url': '',
            'channel': '#alerts'
        },
        'webhook': {
            'enabled': False,
            'url': '',
            'headers': {'Content-Type': 'application/json'}
        }
    },
    'alert_cooldown': 300,  # 5 minutes
    'alert_state_file': '/var/log/flipsync/alerts/alert_state.json'
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/flipsync/alerts/alerting.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('flipsync-alerts')

class AlertManager:
    """Comprehensive alerting and notification management"""
    
    def __init__(self):
        self.alert_state = self._load_alert_state()
    
    def _load_alert_state(self) -> Dict:
        """Load alert state from file"""
        try:
            os.makedirs(os.path.dirname(ALERT_CONFIG['alert_state_file']), exist_ok=True)
            
            if os.path.exists(ALERT_CONFIG['alert_state_file']):
                with open(ALERT_CONFIG['alert_state_file'], 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Failed to load alert state: {e}")
            return {}
    
    def _save_alert_state(self):
        """Save alert state to file"""
        try:
            with open(ALERT_CONFIG['alert_state_file'], 'w') as f:
                json.dump(self.alert_state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save alert state: {e}")
    
    def _should_send_alert(self, alert_key: str) -> bool:
        """Check if alert should be sent based on cooldown"""
        now = time.time()
        last_sent = self.alert_state.get(alert_key, {}).get('last_sent', 0)
        
        return (now - last_sent) > ALERT_CONFIG['alert_cooldown']
    
    def _mark_alert_sent(self, alert_key: str, alert_data: Dict):
        """Mark alert as sent"""
        self.alert_state[alert_key] = {
            'last_sent': time.time(),
            'count': self.alert_state.get(alert_key, {}).get('count', 0) + 1,
            'alert_data': alert_data
        }
        self._save_alert_state()
    
    def analyze_metrics(self, metrics: Dict) -> List[Dict]:
        """Analyze metrics and generate alerts"""
        alerts = []
        
        try:
            # Analyze system metrics
            if 'system' in metrics:
                alerts.extend(self._analyze_system_metrics(metrics['system']))
            
            # Analyze application metrics
            if 'application' in metrics:
                alerts.extend(self._analyze_application_metrics(metrics['application']))
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to analyze metrics: {e}")
            return []
    
    def _analyze_system_metrics(self, system_metrics: Dict) -> List[Dict]:
        """Analyze system metrics for alerts"""
        alerts = []
        
        try:
            # CPU usage alert
            if 'cpu' in system_metrics:
                cpu_percent = system_metrics['cpu'].get('percent', 0)
                if cpu_percent > ALERT_CONFIG['thresholds']['cpu_percent']:
                    alerts.append({
                        'type': 'system',
                        'severity': 'warning' if cpu_percent < 90 else 'critical',
                        'metric': 'cpu_usage',
                        'value': cpu_percent,
                        'threshold': ALERT_CONFIG['thresholds']['cpu_percent'],
                        'message': f"High CPU usage: {cpu_percent}%"
                    })
            
            # Memory usage alert
            if 'memory' in system_metrics:
                memory_percent = system_metrics['memory'].get('percent', 0)
                if memory_percent > ALERT_CONFIG['thresholds']['memory_percent']:
                    alerts.append({
                        'type': 'system',
                        'severity': 'warning' if memory_percent < 95 else 'critical',
                        'metric': 'memory_usage',
                        'value': memory_percent,
                        'threshold': ALERT_CONFIG['thresholds']['memory_percent'],
                        'message': f"High memory usage: {memory_percent}%"
                    })
            
            # Disk usage alert
            if 'disk' in system_metrics:
                disk_percent = system_metrics['disk'].get('percent', 0)
                if disk_percent > ALERT_CONFIG['thresholds']['disk_percent']:
                    alerts.append({
                        'type': 'system',
                        'severity': 'warning' if disk_percent < 95 else 'critical',
                        'metric': 'disk_usage',
                        'value': disk_percent,
                        'threshold': ALERT_CONFIG['thresholds']['disk_percent'],
                        'message': f"High disk usage: {disk_percent}%"
                    })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to analyze system metrics: {e}")
            return []
    
    def _analyze_application_metrics(self, app_metrics: Dict) -> List[Dict]:
        """Analyze application metrics for alerts"""
        alerts = []
        
        try:
            # Backend service alerts
            if 'backend' in app_metrics:
                backend = app_metrics['backend']
                
                if backend.get('status') != 'running':
                    alerts.append({
                        'type': 'application',
                        'severity': 'critical',
                        'metric': 'backend_status',
                        'value': backend.get('status'),
                        'message': f"Backend service is not running: {backend.get('status')}"
                    })
                
                # Backend memory usage
                memory_percent = backend.get('memory_percent', 0)
                if memory_percent > 50:  # Backend-specific threshold
                    alerts.append({
                        'type': 'application',
                        'severity': 'warning',
                        'metric': 'backend_memory',
                        'value': memory_percent,
                        'threshold': 50,
                        'message': f"High backend memory usage: {memory_percent}%"
                    })
            
            # Database alerts
            if 'database' in app_metrics:
                database = app_metrics['database']
                
                if database.get('status') != 'connected':
                    alerts.append({
                        'type': 'application',
                        'severity': 'critical',
                        'metric': 'database_status',
                        'value': database.get('status'),
                        'message': f"Database connection failed: {database.get('status')}"
                    })
                
                # Connection count
                connection_count = database.get('connection_count', 0)
                if connection_count > ALERT_CONFIG['thresholds']['connection_count']:
                    alerts.append({
                        'type': 'application',
                        'severity': 'warning',
                        'metric': 'database_connections',
                        'value': connection_count,
                        'threshold': ALERT_CONFIG['thresholds']['connection_count'],
                        'message': f"High database connection count: {connection_count}"
                    })
            
            # Redis alerts
            if 'redis' in app_metrics:
                redis = app_metrics['redis']
                
                if redis.get('status') != 'connected':
                    alerts.append({
                        'type': 'application',
                        'severity': 'warning',
                        'metric': 'redis_status',
                        'value': redis.get('status'),
                        'message': f"Redis connection failed: {redis.get('status')}"
                    })
            
            # API performance alerts
            if 'api' in app_metrics and 'endpoints' in app_metrics['api']:
                for endpoint, data in app_metrics['api']['endpoints'].items():
                    response_time = data.get('response_time_ms', 0)
                    status_code = data.get('status_code', 0)
                    
                    # Response time alert
                    if response_time > ALERT_CONFIG['thresholds']['response_time_ms']:
                        alerts.append({
                            'type': 'application',
                            'severity': 'warning',
                            'metric': 'api_response_time',
                            'value': response_time,
                            'threshold': ALERT_CONFIG['thresholds']['response_time_ms'],
                            'message': f"Slow API response for {endpoint}: {response_time}ms"
                        })
                    
                    # Status code alert
                    if status_code >= 500:
                        alerts.append({
                            'type': 'application',
                            'severity': 'critical',
                            'metric': 'api_error',
                            'value': status_code,
                            'message': f"API error for {endpoint}: HTTP {status_code}"
                        })
                    elif status_code >= 400:
                        alerts.append({
                            'type': 'application',
                            'severity': 'warning',
                            'metric': 'api_client_error',
                            'value': status_code,
                            'message': f"API client error for {endpoint}: HTTP {status_code}"
                        })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to analyze application metrics: {e}")
            return []
    
    def send_alerts(self, alerts: List[Dict]):
        """Send alerts through configured channels"""
        for alert in alerts:
            alert_key = f"{alert['type']}_{alert['metric']}"
            
            if self._should_send_alert(alert_key):
                self._send_alert_notifications(alert)
                self._mark_alert_sent(alert_key, alert)
                logger.info(f"Alert sent: {alert['message']}")
            else:
                logger.debug(f"Alert suppressed (cooldown): {alert['message']}")
    
    def _send_alert_notifications(self, alert: Dict):
        """Send alert through all enabled notification channels"""
        # Email notification
        if ALERT_CONFIG['notification_channels']['email']['enabled']:
            self._send_email_alert(alert)
        
        # Slack notification
        if ALERT_CONFIG['notification_channels']['slack']['enabled']:
            self._send_slack_alert(alert)
        
        # Webhook notification
        if ALERT_CONFIG['notification_channels']['webhook']['enabled']:
            self._send_webhook_alert(alert)
    
    def _send_email_alert(self, alert: Dict):
        """Send email alert"""
        try:
            email_config = ALERT_CONFIG['notification_channels']['email']
            
            msg = MimeMultipart()
            msg['From'] = email_config['from_email']
            msg['To'] = ', '.join(email_config['to_emails'])
            msg['Subject'] = f"FlipSync Alert - {alert['severity'].upper()}: {alert['metric']}"
            
            body = f"""
FlipSync Alert Notification

Severity: {alert['severity'].upper()}
Type: {alert['type']}
Metric: {alert['metric']}
Message: {alert['message']}
Timestamp: {datetime.utcnow().isoformat()}

Value: {alert.get('value', 'N/A')}
Threshold: {alert.get('threshold', 'N/A')}

This is an automated alert from the FlipSync monitoring system.
"""
            
            msg.attach(MimeText(body, 'plain'))
            
            # Send email (basic implementation - would need SMTP configuration)
            logger.info(f"Email alert prepared: {alert['message']}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    def _send_slack_alert(self, alert: Dict):
        """Send Slack alert"""
        try:
            slack_config = ALERT_CONFIG['notification_channels']['slack']
            
            color = {
                'critical': 'danger',
                'warning': 'warning',
                'info': 'good'
            }.get(alert['severity'], 'warning')
            
            payload = {
                'channel': slack_config['channel'],
                'username': 'FlipSync Monitor',
                'attachments': [{
                    'color': color,
                    'title': f"FlipSync Alert - {alert['severity'].upper()}",
                    'text': alert['message'],
                    'fields': [
                        {'title': 'Type', 'value': alert['type'], 'short': True},
                        {'title': 'Metric', 'value': alert['metric'], 'short': True},
                        {'title': 'Value', 'value': str(alert.get('value', 'N/A')), 'short': True},
                        {'title': 'Threshold', 'value': str(alert.get('threshold', 'N/A')), 'short': True}
                    ],
                    'timestamp': int(time.time())
                }]
            }
            
            response = requests.post(
                slack_config['webhook_url'],
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"Slack alert sent: {alert['message']}")
            
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
    
    def _send_webhook_alert(self, alert: Dict):
        """Send webhook alert"""
        try:
            webhook_config = ALERT_CONFIG['notification_channels']['webhook']
            
            payload = {
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'flipsync-monitor',
                'alert': alert
            }
            
            response = requests.post(
                webhook_config['url'],
                json=payload,
                headers=webhook_config['headers'],
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"Webhook alert sent: {alert['message']}")
            
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")

def main():
    """Main function for alert processing"""
    alert_manager = AlertManager()
    
    # Example usage - in production, this would read from metrics file
    try:
        metrics_file = '/var/log/flipsync/performance/metrics.json'
        
        if os.path.exists(metrics_file):
            # Read latest metrics
            with open(metrics_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    latest_metrics = json.loads(lines[-1])
                    
                    # Analyze and send alerts
                    alerts = alert_manager.analyze_metrics(latest_metrics)
                    if alerts:
                        alert_manager.send_alerts(alerts)
                        logger.info(f"Processed {len(alerts)} alerts")
                    else:
                        logger.info("No alerts generated")
                else:
                    logger.info("No metrics data available")
        else:
            logger.warning(f"Metrics file not found: {metrics_file}")
    
    except Exception as e:
        logger.error(f"Alert processing failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
