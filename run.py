#!/usr/bin/env python3
"""
Main script to run the API Monitor system
"""

import os
import sys
import threading
import time
from app import create_app
from app.monitor import monitor

def run_flask_app():
    """Run the Flask application"""
    app = create_app()
    monitor.init_app(app)
    
    # Add some sample endpoints if database is empty
    with app.app_context():
        from app.models import ApiEndpoints
        if ApiEndpoints.query.count() == 0:
            sample_endpoints = [
                {
                    'name': 'Google',
                    'url': 'https://www.google.com',
                    'method': 'GET',
                    'timeout': 10,
                    'check_interval': 60
                },
                {
                    'name': 'JSONPlaceholder API',
                    'url': 'https://jsonplaceholder.typicode.com/posts/1',
                    'method': 'GET',
                    'timeout': 15,
                    'check_interval': 120
                },
                {
                    'name': 'HTTPBin Status',
                    'url': 'https://httpbin.org/status/200',
                    'method': 'GET',
                    'timeout': 10,
                    'check_interval': 300
                }
            ]
            
            for endpoint_data in sample_endpoints:
                monitor.add_endpoint(**endpoint_data)
            
            print("Added sample endpoints for testing")
    
    # Start monitoring
    monitor.start_monitoring()
    
    print("Starting Flask server...")
    print("API endpoints available at: http://localhost:5000/api/")
    print("Health check: http://localhost:5000/api/health")
    print("Metrics: http://localhost:5000/api/metrics")
    print("Endpoints: http://localhost:5000/api/endpoints")
    
    # Run Flask app
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)

def run_flet_ui():
    """Run the Flet desktop UI"""
    # Wait a moment for Flask to start
    time.sleep(3)
    
    print("Starting Flet UI...")
    try:
        import flet as ft
        from flet_ui.main import main
        ft.app(target=main, view=ft.AppView.FLET_APP)
    except ImportError:
        print("Flet not installed. Run: pip install -r requirements.txt")
        print("You can still use the web API at http://localhost:5000/api/")

def main():
    """Main entry point"""
    print("=" * 50)
    print("API Monitor System")
    print("=" * 50)
    
    # Ensure instance directory exists
    os.makedirs('instance', exist_ok=True)
    
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask_app, daemon=True)
    flask_thread.start()
    
    # Start Flet UI in main thread
    try:
        run_flet_ui()
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"Error running UI: {e}")
        print("Flask API is still running at http://localhost:5000/api/")
        
        # Keep Flask running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            sys.exit(0)

if __name__ == "__main__":
    main()