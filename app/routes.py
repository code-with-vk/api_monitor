from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from app.models import ApiMetrics, ApiEndpoints
from app import db

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})

@bp.route('/metrics', methods=['GET'])
def get_metrics():
    """Get API metrics for Grafana"""
    # Query parameters
    endpoint_name = request.args.get('endpoint')
    hours = request.args.get('hours', 24, type=int)
    limit = request.args.get('limit', 1000, type=int)
    
    # Calculate time range
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Build query
    query = ApiMetrics.query.filter(ApiMetrics.timestamp >= start_time)
    
    if endpoint_name:
        query = query.filter(ApiMetrics.endpoint_name == endpoint_name)
    
    metrics = query.order_by(desc(ApiMetrics.timestamp)).limit(limit).all()
    
    return jsonify([metric.to_dict() for metric in metrics])

@bp.route('/metrics/summary', methods=['GET'])
def get_metrics_summary():
    """Get summary statistics for all endpoints"""
    hours = request.args.get('hours', 24, type=int)
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Get summary by endpoint
    summary_query = db.session.query(
        ApiMetrics.endpoint_name,
        func.count(ApiMetrics.id).label('total_checks'),
        func.sum(ApiMetrics.is_success.cast(db.Integer)).label('successful_checks'),
        func.avg(ApiMetrics.response_time).label('avg_response_time'),
        func.min(ApiMetrics.response_time).label('min_response_time'),
        func.max(ApiMetrics.response_time).label('max_response_time'),
        func.max(ApiMetrics.timestamp).label('last_check')
    ).filter(
        ApiMetrics.timestamp >= start_time
    ).group_by(ApiMetrics.endpoint_name).all()
    
    summaries = []
    for row in summary_query:
        success_rate = (row.successful_checks / row.total_checks * 100) if row.total_checks > 0 else 0
        
        summaries.append({
            'endpoint_name': row.endpoint_name,
            'total_checks': row.total_checks,
            'successful_checks': row.successful_checks,
            'failed_checks': row.total_checks - row.successful_checks,
            'success_rate': round(success_rate, 2),
            'avg_response_time': round(row.avg_response_time, 3) if row.avg_response_time else 0,
            'min_response_time': round(row.min_response_time, 3) if row.min_response_time else 0,
            'max_response_time': round(row.max_response_time, 3) if row.max_response_time else 0,
            'last_check': row.last_check.isoformat() if row.last_check else None
        })
    
    return jsonify(summaries)

@bp.route('/endpoints', methods=['GET'])
def get_endpoints():
    """Get all configured endpoints"""
    endpoints = ApiEndpoints.query.all()
    return jsonify([endpoint.to_dict() for endpoint in endpoints])

@bp.route('/endpoints', methods=['POST'])
def create_endpoint():
    """Create a new endpoint"""
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('url'):
        return jsonify({"error": "Name and URL are required"}), 400
    
    # Check if name already exists
    existing = ApiEndpoints.query.filter_by(name=data['name']).first()
    if existing:
        return jsonify({"error": "Endpoint name already exists"}), 400
    
    endpoint = ApiEndpoints(
        name=data['name'],
        url=data['url'],
        method=data.get('method', 'GET').upper(),
        headers=data.get('headers'),
        body=data.get('body'),
        timeout=data.get('timeout', 30),
        check_interval=data.get('check_interval', 300),
        is_active=data.get('is_active', True)
    )
    
    db.session.add(endpoint)
    db.session.commit()
    
    return jsonify(endpoint.to_dict()), 201

@bp.route('/endpoints/<int:endpoint_id>', methods=['PUT'])
def update_endpoint(endpoint_id):
    """Update an existing endpoint"""
    endpoint = ApiEndpoints.query.get_or_404(endpoint_id)
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Update fields
    if 'name' in data:
        # Check if new name already exists (excluding current endpoint)
        existing = ApiEndpoints.query.filter(
            ApiEndpoints.name == data['name'],
            ApiEndpoints.id != endpoint_id
        ).first()
        if existing:
            return jsonify({"error": "Endpoint name already exists"}), 400
        endpoint.name = data['name']
    
    if 'url' in data:
        endpoint.url = data['url']
    if 'method' in data:
        endpoint.method = data['method'].upper()
    if 'headers' in data:
        endpoint.headers = data['headers']
    if 'body' in data:
        endpoint.body = data['body']
    if 'timeout' in data:
        endpoint.timeout = data['timeout']
    if 'check_interval' in data:
        endpoint.check_interval = data['check_interval']
    if 'is_active' in data:
        endpoint.is_active = data['is_active']
    
    db.session.commit()
    return jsonify(endpoint.to_dict())

@bp.route('/endpoints/<int:endpoint_id>', methods=['DELETE'])
def delete_endpoint(endpoint_id):
    """Delete an endpoint"""
    endpoint = ApiEndpoints.query.get_or_404(endpoint_id)
    
    # Delete associated metrics
    ApiMetrics.query.filter_by(endpoint_name=endpoint.name).delete()
    
    # Delete endpoint
    db.session.delete(endpoint)
    db.session.commit()
    
    return jsonify({"message": "Endpoint deleted successfully"})

@bp.route('/endpoints/<int:endpoint_id>/toggle', methods=['POST'])
def toggle_endpoint(endpoint_id):
    """Toggle endpoint active status"""
    endpoint = ApiEndpoints.query.get_or_404(endpoint_id)
    endpoint.is_active = not endpoint.is_active
    db.session.commit()
    
    return jsonify({
        "message": f"Endpoint {'activated' if endpoint.is_active else 'deactivated'}",
        "endpoint": endpoint.to_dict()
    })

@bp.route('/metrics/grafana', methods=['GET'])
def grafana_metrics():
    """Grafana-compatible metrics endpoint"""
    # This endpoint formats data specifically for Grafana queries
    endpoint_name = request.args.get('endpoint')
    hours = request.args.get('hours', 24, type=int)
    
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    query = ApiMetrics.query.filter(ApiMetrics.timestamp >= start_time)
    if endpoint_name:
        query = query.filter(ApiMetrics.endpoint_name == endpoint_name)
    
    metrics = query.order_by(ApiMetrics.timestamp).all()
    
    # Format for Grafana
    datapoints = []
    for metric in metrics:
        timestamp_ms = int(metric.timestamp.timestamp() * 1000)
        datapoints.append({
            "target": metric.endpoint_name,
            "datapoints": [
                [metric.response_time, timestamp_ms],
                [1 if metric.is_success else 0, timestamp_ms]  # Success as 1/0
            ]
        })
    
    return jsonify(datapoints)