import json
import os
import time
from datetime import datetime
import logging

class AlertLogger:
    """Real-time alert logging system for suspicious content"""
    
    def __init__(self, log_dir=None):
        """Initialize alert logger
        
        Args:
            log_dir: Custom directory for alert logs
        """
        # Set up base directory
        if log_dir:
            self.log_dir = log_dir
        else:
            self.log_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "outputs", "alerts"
            )
        
        # Create directories if they don't exist
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Set up logging
        self.logger = self._setup_logger()
        
        # Configure alert storage
        self.alerts_file = os.path.join(self.log_dir, f"alerts_{datetime.now().strftime('%Y%m%d')}.json")
        self.alerts = self._load_existing_alerts()
        
        print(f"🔔 Alert system initialized. Logs will be saved to {self.log_dir}")
    
    def _setup_logger(self):
        """Set up Python logger for alerts"""
        logger = logging.getLogger("darkweb_alerts")
        logger.setLevel(logging.INFO)
        
        # Create file handler
        log_file = os.path.join(self.log_dir, f"alerts_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_file)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def close(self):
        """Close log handlers to release file locks"""
        for handler in self.logger.handlers[:]:
            handler.flush()
            handler.close()
            self.logger.removeHandler(handler)
    
    def _load_existing_alerts(self):
        """Load existing alerts from file"""
        if os.path.exists(self.alerts_file):
            try:
                with open(self.alerts_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, Exception):
                return []
        return []
    
    def _save_alerts(self):
        """Save alerts to file"""
        with open(self.alerts_file, 'w', encoding='utf-8') as f:
            json.dump(self.alerts, f, indent=2)
    
    def log_alert(self, url, category, severity, snippet, timestamp=None):
        """Log a new alert
        
        Args:
            url: URL where content was found
            category: Category of alert (e.g., 'Drugs', 'Weapons')
            severity: Alert severity (1-5, with 5 being highest)
            snippet: Text snippet that triggered the alert
            timestamp: Optional timestamp (defaults to now)
        """
        if not timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        alert = {
            "url": url,
            "category": category,
            "severity": severity,
            "snippet": snippet,
            "timestamp": timestamp
        }
        
        # Add to in-memory alerts
        self.alerts.append(alert)
        
        # Save to disk
        self._save_alerts()
        
        # Log to Python logger
        log_message = f"ALERT [{category}] [Severity: {severity}] URL: {url}"
        
        if severity >= 4:
            self.logger.critical(log_message)
        elif severity == 3:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        print(f"🚨 New alert: {category} [Severity: {severity}] - {url}")
        
        return alert
    
    def get_alerts(self, category=None, min_severity=0, limit=None):
        """Get alerts filtered by category and severity
        
        Args:
            category: Filter by category
            min_severity: Minimum severity level
            limit: Maximum number of alerts to return
        
        Returns:
            list: Filtered alerts
        """
        filtered = self.alerts
        
        if category:
            filtered = [a for a in filtered if a["category"] == category]
            
        if min_severity > 0:
            filtered = [a for a in filtered if a["severity"] >= min_severity]
            
        # Sort by timestamp (newest first)
        filtered.sort(key=lambda x: x["timestamp"], reverse=True)
        
        if limit:
            filtered = filtered[:limit]
            
        return filtered
    
    def get_alert_stats(self):
        """Get statistics about alerts
        
        Returns:
            dict: Statistics about alerts
        """
        if not self.alerts:
            return {
                "total": 0,
                "categories": {},
                "severity_levels": {}
            }
            
        # Count by category
        categories = {}
        for alert in self.alerts:
            cat = alert["category"]
            if cat in categories:
                categories[cat] += 1
            else:
                categories[cat] = 1
                
        # Count by severity
        severity_levels = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for alert in self.alerts:
            severity = alert["severity"]
            if severity in severity_levels:
                severity_levels[severity] += 1
        
        return {
            "total": len(self.alerts),
            "categories": categories,
            "severity_levels": severity_levels
        } 