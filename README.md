# API Monitor System

A powerful and user-friendly application for monitoring API endpoints and their health status. This system provides both a desktop GUI interface and a web API for managing and monitoring multiple API endpoints in real-time.

## Features

- **Desktop GUI Interface**: Built with Flet (Flutter-based) for a modern, responsive experience
- **Real-time Monitoring**: Continuously monitors API endpoints and tracks their performance
- **Comprehensive Metrics**:
  - Success/failure rates
  - Response times (min, max, average)
  - Total checks performed
  - Last check timestamp
  
- **Endpoint Management**:
  - Add new endpoints with custom configurations
  - Toggle endpoint monitoring
  - Delete endpoints
  - Support for different HTTP methods (GET, POST, PUT, DELETE)
  - Custom headers and request body support

- **Visual Status Indicators**:
  - Color-coded status indicators
  - Success rate visualization
  - Connection status monitoring

## Technical Details

- **Backend**: Flask-based RESTful API
- **Frontend**: Flet (Python UI framework based on Flutter)
- **Database**: SQLite for data persistence
- **Monitoring**: Thread-based continuous monitoring system
- **Cross-platform**: Works on Windows, Linux, and macOS

## Getting Started

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python run.py
```

3. Access the system:
- Desktop UI will launch automatically
- Web API available at http://localhost:5000/api/

## API Endpoints

- `GET /api/health`: Check API server status
- `GET /api/endpoints`: List all configured endpoints
- `POST /api/endpoints`: Add new endpoint
- `DELETE /api/endpoints/<id>`: Delete endpoint
- `POST /api/endpoints/<id>/toggle`: Toggle endpoint monitoring
- `GET /api/metrics`: Get monitoring metrics
- `GET /api/metrics/summary`: Get metrics summary

## Configuration Options

- **Endpoint Settings**:
  - Name: Friendly name for the endpoint
  - URL: Target API endpoint URL
  - Method: HTTP method (GET/POST/PUT/DELETE)
  - Timeout: Request timeout in seconds
  - Check Interval: Monitoring frequency in seconds
  - Headers: Optional custom HTTP headers (JSON format)
  - Body: Optional request body (JSON format)

## Requirements

- Python 3.7+
- Flet
- Flask
- Requests
- Threading support
- Internet connection for monitoring external APIs

## Use Cases

- API Service Monitoring
- Website Uptime Tracking
- Backend Service Health Checks
- API Performance Analysis
- SLA Compliance Monitoring
