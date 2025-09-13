"""
Security middleware for production deployment
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time
import logging
from typing import Callable

logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

class SecurityMiddleware:
    """Security middleware for request validation and rate limiting"""
    
    def __init__(self, app):
        self.app = app
        self.request_count = {}
        self.blocked_ips = set()
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Check for blocked IPs
            client_ip = get_remote_address(request)
            if client_ip in self.blocked_ips:
                response = JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"error": "IP blocked due to suspicious activity"}
                )
                await response(scope, receive, send)
                return
            
            # Basic request validation
            if not await self._validate_request(request):
                response = JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"error": "Invalid request"}
                )
                await response(scope, receive, send)
                return
            
            # Log request
            await self._log_request(request)
        
        await self.app(scope, receive, send)
    
    async def _validate_request(self, request: Request) -> bool:
        """Validate incoming requests"""
        try:
            # Check for suspicious headers
            suspicious_headers = [
                'x-forwarded-for', 'x-real-ip', 'x-cluster-client-ip',
                'x-forwarded', 'x-forwarded-proto', 'x-forwarded-host'
            ]
            
            for header in suspicious_headers:
                if header in request.headers:
                    value = request.headers[header]
                    # Basic validation for common injection patterns
                    if any(pattern in value.lower() for pattern in ['<script', 'javascript:', 'data:']):
                        logger.warning(f"Suspicious header detected: {header}={value}")
                        return False
            
            # Check request size
            content_length = request.headers.get('content-length')
            if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
                logger.warning(f"Request too large: {content_length} bytes")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Request validation error: {e}")
            return False
    
    async def _log_request(self, request: Request):
        """Log request details for monitoring"""
        try:
            client_ip = get_remote_address(request)
            user_agent = request.headers.get('user-agent', 'Unknown')
            method = request.method
            url = str(request.url)
            
            # Log request
            logger.info(f"Request: {method} {url} from {client_ip} - {user_agent}")
            
            # Track request count per IP
            current_time = time.time()
            if client_ip not in self.request_count:
                self.request_count[client_ip] = []
            
            # Clean old requests (older than 1 minute)
            self.request_count[client_ip] = [
                req_time for req_time in self.request_count[client_ip]
                if current_time - req_time < 60
            ]
            
            # Add current request
            self.request_count[client_ip].append(current_time)
            
            # Block IP if too many requests (more than 100 per minute)
            if len(self.request_count[client_ip]) > 100:
                self.blocked_ips.add(client_ip)
                logger.warning(f"IP {client_ip} blocked due to rate limiting")
                
        except Exception as e:
            logger.error(f"Request logging error: {e}")

def setup_rate_limiting(app):
    """Setup rate limiting for the application"""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    return app
