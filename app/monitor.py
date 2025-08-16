import requests
import time
import json
import logging
from datetime import datetime
from app import db
from app.models import ApiMetrics, ApiEndpoints
from apscheduler.schedulers.background import BackgroundScheduler
from flask import current_app

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ApiMonitor:
    def __init__(self, app=None):
        self.scheduler = BackgroundScheduler()
        self.app = app
        
    def init_app(self, app):
        self.app = app
        
    def start_monitoring(self):
        """Start the background scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("API monitoring started")
            self._schedule_checks()
    
    def stop_monitoring(self):
        """Stop the background scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("API monitoring stopped")
    
    def _schedule_checks(self):
        """Schedule checks for all active endpoints"""
        with self.app.app_context():
            endpoints = ApiEndpoints.query.filter_by(is_active=True).all()
            
            # Remove existing jobs
            for job in self.scheduler.get_jobs():
                self.scheduler.remove_job(job.id)
            
            # Add new jobs for active endpoints
            for endpoint in endpoints:
                self.scheduler.add_job(
                    func=self._check_endpoint,
                    trigger="interval",
                    seconds=endpoint.check_interval,
                    id=f"check_{endpoint.id}",
                    args=[endpoint.id],
                    replace_existing=True
                )
                logger.info(f"Scheduled checks for {endpoint.name} every {endpoint.check_interval} seconds")
    
    def _check_endpoint(self, endpoint_id):
        """Check a single endpoint and save metrics"""
        with self.app.app_context():
            endpoint = ApiEndpoints.query.get(endpoint_id)
            if not endpoint or not endpoint.is_active:
                return
            
            start_time = time.time()
            
            try:
                # Prepare headers
                headers = {}
                if endpoint.headers:
                    headers = json.loads(endpoint.headers)
                
                # Prepare body
                data = None
                if endpoint.body and endpoint.method.upper() in ['POST', 'PUT', 'PATCH']:
                    data = json.loads(endpoint.body)
                
                # Make request
                response = requests.request(
                    method=endpoint.method,
                    url=endpoint.url,
                    headers=headers,
                    json=data,
                    timeout=endpoint.timeout
                )
                
                response_time = time.time() - start_time
                is_success = 200 <= response.status_code < 300
                error_message = None if is_success else response.text[:500]
                
                # Save metrics
                metric = ApiMetrics(
                    endpoint_name=endpoint.name,
                    endpoint_url=endpoint.url,
                    response_time=response_time,
                    status_code=response.status_code,
                    is_success=is_success,
                    error_message=error_message
                )
                
                db.session.add(metric)
                db.session.commit()
                
                logger.info(f"Checked {endpoint.name}: {response.status_code} ({response_time:.2f}s)")
                
            except requests.exceptions.Timeout:
                response_time = time.time() - start_time
                self._save_error_metric(endpoint, response_time, 0, "Request timeout")
                
            except requests.exceptions.ConnectionError:
                response_time = time.time() - start_time
                self._save_error_metric(endpoint, response_time, 0, "Connection error")
                
            except Exception as e:
                response_time = time.time() - start_time
                self._save_error_metric(endpoint, response_time, 0, str(e))
    
    def _save_error_metric(self, endpoint, response_time, status_code, error_message):
        """Save error metrics to database"""
        metric = ApiMetrics(
            endpoint_name=endpoint.name,
            endpoint_url=endpoint.url,
            response_time=response_time,
            status_code=status_code,
            is_success=False,
            error_message=error_message
        )
        
        db.session.add(metric)
        db.session.commit()
        
        logger.error(f"Error checking {endpoint.name}: {error_message}")
    
    def add_endpoint(self, name, url, method='GET', headers=None, body=None, 
                    timeout=30, check_interval=300):
        """Add a new endpoint to monitor"""
        with self.app.app_context():
            endpoint = ApiEndpoints(
                name=name,
                url=url,
                method=method.upper(),
                headers=json.dumps(headers) if headers else None,
                body=json.dumps(body) if body else None,
                timeout=timeout,
                check_interval=check_interval,
                is_active=True
            )
            
            db.session.add(endpoint)
            db.session.commit()
            
            # Reschedule checks to include new endpoint
            if self.scheduler.running:
                self._schedule_checks()
            
            logger.info(f"Added endpoint: {name}")
            return endpoint
    
    def remove_endpoint(self, endpoint_id):
        """Remove an endpoint from monitoring"""
        with self.app.app_context():
            endpoint = ApiEndpoints.query.get(endpoint_id)
            if endpoint:
                # Remove scheduled job
                job_id = f"check_{endpoint_id}"
                try:
                    self.scheduler.remove_job(job_id)
                except:
                    pass
                
                # Remove from database
                db.session.delete(endpoint)
                db.session.commit()
                
                logger.info(f"Removed endpoint: {endpoint.name}")
    
    def toggle_endpoint(self, endpoint_id):
        """Toggle endpoint active status"""
        with self.app.app_context():
            endpoint = ApiEndpoints.query.get(endpoint_id)
            if endpoint:
                endpoint.is_active = not endpoint.is_active
                db.session.commit()
                
                # Reschedule checks
                if self.scheduler.running:
                    self._schedule_checks()
                
                status = "activated" if endpoint.is_active else "deactivated"
                logger.info(f"Endpoint {endpoint.name} {status}")
                return endpoint

# Global monitor instance
monitor = ApiMonitor()