import flet as ft
import requests
import json
import threading
import time
from datetime import datetime, timedelta

class ApiMonitorUI:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "API Monitor Control Panel"
        self.page.window_width = 1000
        self.page.window_height = 700
        self.page.theme_mode = ft.ThemeMode.LIGHT
        
        # API base URL
        self.api_base = "http://localhost:5000/api"
        
        # UI components
        self.endpoints_list = ft.Column()
        self.metrics_display = ft.Column()
        self.status_text = ft.Text("Disconnected", color="red")
        
        # Setup UI
        self.setup_ui()
        
        # Start monitoring connection
        self.check_connection()
    
    def setup_ui(self):
        """Setup the main UI components"""
        
        # Header
        header = ft.Container(
            content=ft.Row([
                ft.Text("API Monitor", size=24, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                self.status_text
            ]),
            padding=20,
            bgcolor=ft.colors.BLUE_50
        )
        
        # Tabs
        tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(
                    text="Endpoints",
                    content=self.create_endpoints_tab()
                ),
                ft.Tab(
                    text="Metrics",
                    content=self.create_metrics_tab()
                ),
                ft.Tab(
                    text="Add Endpoint",
                    content=self.create_add_endpoint_tab()
                )
            ]
        )
        
        self.page.add(header, tabs)
    
    def create_endpoints_tab(self):
        """Create the endpoints management tab"""
        
        refresh_btn = ft.ElevatedButton(
            "Refresh",
            icon=ft.icons.REFRESH,
            on_click=self.refresh_endpoints
        )
        
        content = ft.Column([
            ft.Row([
                ft.Text("Configured Endpoints", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                refresh_btn
            ]),
            ft.Divider(),
            ft.Container(
                content=ft.Column([self.endpoints_list]),
                height=400,
                expand=True
            )
        ], scroll=ft.ScrollMode.AUTO)
        
        return ft.Container(content=content, padding=20)
    
    def create_metrics_tab(self):
        """Create the metrics display tab"""
        
        refresh_metrics_btn = ft.ElevatedButton(
            "Refresh Metrics",
            icon=ft.icons.ANALYTICS,
            on_click=self.refresh_metrics
        )
        
        content = ft.Column([
            ft.Row([
                ft.Text("Metrics Summary", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                refresh_metrics_btn
            ]),
            ft.Divider(),
            ft.Container(
                content=ft.Column([self.metrics_display]),
                height=400,
                expand=True
            )
        ], scroll=ft.ScrollMode.AUTO)
        
        return ft.Container(content=content, padding=20)
    
    def create_add_endpoint_tab(self):
        """Create the add endpoint tab"""
        
        # Form fields
        self.name_field = ft.TextField(label="Endpoint Name", width=300)
        self.url_field = ft.TextField(label="URL", width=400)
        self.method_dropdown = ft.Dropdown(
            label="Method",
            width=100,
            options=[
                ft.dropdown.Option("GET"),
                ft.dropdown.Option("POST"),
                ft.dropdown.Option("PUT"),
                ft.dropdown.Option("DELETE")
            ],
            value="GET"
        )
        self.timeout_field = ft.TextField(label="Timeout (seconds)", value="30", width=150)
        self.interval_field = ft.TextField(label="Check Interval (seconds)", value="300", width=200)
        self.headers_field = ft.TextField(
            label="Headers (JSON)",
            multiline=True,
            height=100,
            width=400
        )
        self.body_field = ft.TextField(
            label="Body (JSON)",
            multiline=True,
            height=100,
            width=400
        )
        
        add_btn = ft.ElevatedButton(
            "Add Endpoint",
            icon=ft.icons.ADD,
            on_click=self.add_endpoint
        )
        
        content = ft.Column([
            ft.Text("Add New Endpoint", size=18, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Row([self.name_field, self.method_dropdown]),
            self.url_field,
            ft.Row([self.timeout_field, self.interval_field]),
            ft.Text("Optional Fields:", weight=ft.FontWeight.BOLD),
            self.headers_field,
            self.body_field,
            ft.Container(height=20),
            add_btn
        ], scroll=ft.ScrollMode.AUTO)
        
        return ft.Container(content=content, padding=20)
    
    def check_connection(self):
        """Check connection to Flask API"""
        def check():
            while True:
                try:
                    response = requests.get(f"{self.api_base}/health", timeout=5)
                    if response.status_code == 200:
                        self.status_text.value = "Connected"
                        self.status_text.color = "green"
                    else:
                        self.status_text.value = "API Error"
                        self.status_text.color = "orange"
                except:
                    self.status_text.value = "Disconnected"
                    self.status_text.color = "red"
                
                self.page.update()
                time.sleep(5)
        
        thread = threading.Thread(target=check, daemon=True)
        thread.start()
    
    def refresh_endpoints(self, e=None):
        """Refresh the endpoints list"""
        try:
            response = requests.get(f"{self.api_base}/endpoints")
            if response.status_code == 200:
                endpoints = response.json()
                self.endpoints_list.controls.clear()
                
                for endpoint in endpoints:
                    status_color = "green" if endpoint['is_active'] else "red"
                    status_text = "Active" if endpoint['is_active'] else "Inactive"
                    
                    endpoint_card = ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(endpoint['name'], weight=ft.FontWeight.BOLD, size=16),
                                    ft.Container(expand=True),
                                    ft.Text(status_text, color=status_color, weight=ft.FontWeight.BOLD)
                                ]),
                                ft.Text(f"URL: {endpoint['url']}", size=12),
                                ft.Text(f"Method: {endpoint['method']} | Interval: {endpoint['check_interval']}s", size=12),
                                ft.Row([
                                    ft.ElevatedButton(
                                        "Toggle",
                                        on_click=lambda e, ep_id=endpoint['id']: self.toggle_endpoint(ep_id),
                                        bgcolor=ft.colors.ORANGE_100
                                    ),
                                    ft.ElevatedButton(
                                        "Delete",
                                        on_click=lambda e, ep_id=endpoint['id']: self.delete_endpoint(ep_id),
                                        bgcolor=ft.colors.RED_100
                                    )
                                ])
                            ]),
                            padding=15
                        )
                    )
                    self.endpoints_list.controls.append(endpoint_card)
                
                self.page.update()
            else:
                self.show_error("Failed to fetch endpoints")
        except Exception as ex:
            self.show_error(f"Error: {str(ex)}")
    
    def refresh_metrics(self, e=None):
        """Refresh the metrics display"""
        try:
            response = requests.get(f"{self.api_base}/metrics/summary")
            if response.status_code == 200:
                summaries = response.json()
                self.metrics_display.controls.clear()
                
                for summary in summaries:
                    success_color = "green" if summary['success_rate'] > 95 else "orange" if summary['success_rate'] > 80 else "red"
                    
                    metrics_card = ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text(summary['endpoint_name'], weight=ft.FontWeight.BOLD, size=16),
                                ft.Row([
                                    ft.Column([
                                        ft.Text(f"Success Rate: {summary['success_rate']}%", color=success_color, weight=ft.FontWeight.BOLD),
                                        ft.Text(f"Total Checks: {summary['total_checks']}"),
                                        ft.Text(f"Failed: {summary['failed_checks']}")
                                    ], tight=True),
                                    ft.Container(width=50),
                                    ft.Column([
                                        ft.Text(f"Avg Response: {summary['avg_response_time']}s"),
                                        ft.Text(f"Min: {summary['min_response_time']}s"),
                                        ft.Text(f"Max: {summary['max_response_time']}s")
                                    ], tight=True)
                                ]),
                                ft.Text(f"Last Check: {summary['last_check'][:19] if summary['last_check'] else 'Never'}", size=10)
                            ]),
                            padding=15
                        )
                    )
                    self.metrics_display.controls.append(metrics_card)
                
                self.page.update()
            else:
                self.show_error("Failed to fetch metrics")
        except Exception as ex:
            self.show_error(f"Error: {str(ex)}")
    
    def add_endpoint(self, e):
        """Add a new endpoint"""
        try:
            # Validate required fields
            if not self.name_field.value or not self.url_field.value:
                self.show_error("Name and URL are required")
                return
            
            # Prepare data
            data = {
                "name": self.name_field.value,
                "url": self.url_field.value,
                "method": self.method_dropdown.value,
                "timeout": int(self.timeout_field.value or 30),
                "check_interval": int(self.interval_field.value or 300)
            }
            
            # Add optional fields
            if self.headers_field.value:
                try:
                    data["headers"] = self.headers_field.value
                    json.loads(self.headers_field.value)  # Validate JSON
                except json.JSONDecodeError:
                    self.show_error("Invalid JSON in headers field")
                    return
            
            if self.body_field.value:
                try:
                    data["body"] = self.body_field.value
                    json.loads(self.body_field.value)  # Validate JSON
                except json.JSONDecodeError:
                    self.show_error("Invalid JSON in body field")
                    return
            
            # Send request
            response = requests.post(f"{self.api_base}/endpoints", json=data)
            
            if response.status_code == 201:
                self.show_success("Endpoint added successfully!")
                # Clear form
                self.name_field.value = ""
                self.url_field.value = ""
                self.method_dropdown.value = "GET"
                self.timeout_field.value = "30"
                self.interval_field.value = "300"
                self.headers_field.value = ""
                self.body_field.value = ""
                self.page.update()
                # Refresh endpoints list
                self.refresh_endpoints()
            else:
                error_msg = response.json().get('error', 'Unknown error')
                self.show_error(f"Failed to add endpoint: {error_msg}")
                
        except ValueError:
            self.show_error("Timeout and interval must be valid numbers")
        except Exception as ex:
            self.show_error(f"Error: {str(ex)}")
    
    def toggle_endpoint(self, endpoint_id):
        """Toggle endpoint active status"""
        try:
            response = requests.post(f"{self.api_base}/endpoints/{endpoint_id}/toggle")
            if response.status_code == 200:
                self.refresh_endpoints()
            else:
                self.show_error("Failed to toggle endpoint")
        except Exception as ex:
            self.show_error(f"Error: {str(ex)}")
    
    def delete_endpoint(self, endpoint_id):
        """Delete an endpoint"""
        def confirm_delete(e):
            try:
                response = requests.delete(f"{self.api_base}/endpoints/{endpoint_id}")
                if response.status_code == 200:
                    self.show_success("Endpoint deleted successfully!")
                    self.refresh_endpoints()
                else:
                    self.show_error("Failed to delete endpoint")
            except Exception as ex:
                self.show_error(f"Error: {str(ex)}")
            dialog.open = False
            self.page.update()
        
        def cancel_delete(e):
            dialog.open = False
            self.page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Delete"),
            content=ft.Text("Are you sure you want to delete this endpoint? This will also delete all associated metrics."),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_delete),
                ft.TextButton("Delete", on_click=confirm_delete),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def show_error(self, message):
        """Show error snackbar"""
        snackbar = ft.SnackBar(
            content=ft.Text(message, color="white"),
            bgcolor="red"
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()
    
    def show_success(self, message):
        """Show success snackbar"""
        snackbar = ft.SnackBar(
            content=ft.Text(message, color="white"),
            bgcolor="green"
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()

def main(page: ft.Page):
    app = ApiMonitorUI(page)
    app.refresh_endpoints()
    app.refresh_metrics()

if __name__ == "__main__":
    ft.app(target=main)