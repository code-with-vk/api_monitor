from app import db
from datetime import datetime

class ApiMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    endpoint_name = db.Column(db.String(100), nullable=False)
    endpoint_url = db.Column(db.String(500), nullable=False)
    response_time = db.Column(db.Float, nullable=False)
    status_code = db.Column(db.Integer, nullable=False)
    is_success = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    error_message = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<ApiMetrics {self.endpoint_name}: {self.status_code}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'endpoint_name': self.endpoint_name,
            'endpoint_url': self.endpoint_url,
            'response_time': self.response_time,
            'status_code': self.status_code,
            'is_success': self.is_success,
            'timestamp': self.timestamp.isoformat(),
            'error_message': self.error_message
        }

class ApiEndpoints(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    url = db.Column(db.String(500), nullable=False)
    method = db.Column(db.String(10), nullable=False, default='GET')
    headers = db.Column(db.Text, nullable=True)  # JSON string
    body = db.Column(db.Text, nullable=True)     # JSON string
    timeout = db.Column(db.Integer, nullable=False, default=30)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    check_interval = db.Column(db.Integer, nullable=False, default=300)  # seconds
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ApiEndpoint {self.name}: {self.url}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'method': self.method,
            'headers': self.headers,
            'body': self.body,
            'timeout': self.timeout,
            'is_active': self.is_active,
            'check_interval': self.check_interval,
            'created_at': self.created_at.isoformat()
        }