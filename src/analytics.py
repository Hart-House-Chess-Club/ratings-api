import requests
import json
import asyncio
from datetime import datetime
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class GoogleAnalyticsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, ga_tracking_id: str = "G-JSFHZ4X5YL"):
        super().__init__(app)
        self.ga_tracking_id = ga_tracking_id
        self.measurement_url = "https://www.google-analytics.com/mp/collect"
        
    async def dispatch(self, request: Request, call_next):
        # Track the request start time
        start_time = datetime.now()
        
        # Process the request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = (datetime.now() - start_time).total_seconds()
        
        # Send analytics data asynchronously (fire and forget)
        asyncio.create_task(self._send_analytics_event(request, response, process_time))
        
        return response
    
    async def _send_analytics_event(self, request: Request, response, process_time: float):
        try:
            # Generate a session ID based on client IP (simplified)
            client_ip = request.client.host if request.client else "unknown"
            session_id = hash(client_ip) % 2147483647  # Keep it positive 32-bit int
            
            # Prepare the analytics payload
            payload = {
                "client_id": str(abs(session_id)),
                "events": [{
                    "name": "api_request",
                    "params": {
                        "api_endpoint": str(request.url.path),
                        "http_method": request.method,
                        "status_code": response.status_code,
                        "response_time_ms": int(process_time * 1000),
                        "user_agent": request.headers.get("user-agent", "unknown"),
                        "referer": request.headers.get("referer", "direct"),
                        "engagement_time_msec": int(process_time * 1000)
                    }
                }]
            }
            
            # Send to Google Analytics 4
            analytics_url = f"{self.measurement_url}?measurement_id={self.ga_tracking_id}&api_secret=YOUR_API_SECRET"
            
            # Note: For production, you should use a proper API secret from Google Analytics
            # For now, we'll use the gtag method via the web interface
            
        except Exception as e:
            # Silently fail - don't let analytics errors affect the API
            pass
