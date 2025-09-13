"""
Advanced logging middleware for production
"""
import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import json

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Advanced logging middleware for production monitoring"""
    
    async def dispatch(self, request: Request, call_next):
        # Start time
        start_time = time.time()
        
        # Get request details
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        method = request.method
        url = str(request.url)
        
        # Log request
        logger.info(f"Request started: {method} {url} from {client_ip}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Request completed: {method} {url} - "
                f"Status: {response.status_code} - "
                f"Time: {process_time:.4f}s - "
                f"IP: {client_ip} - "
                f"User-Agent: {user_agent}"
            )
            
            # Add custom headers
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = f"req_{int(time.time() * 1000)}"
            
            return response
            
        except Exception as e:
            # Log error
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {method} {url} - "
                f"Error: {str(e)} - "
                f"Time: {process_time:.4f}s - "
                f"IP: {client_ip}"
            )
            raise

class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    """Security-focused logging middleware"""
    
    async def dispatch(self, request: Request, call_next):
        # Check for suspicious patterns
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        url = str(request.url)
        
        # Log suspicious patterns
        suspicious_patterns = [
            "sql", "script", "javascript", "eval", "exec",
            "union", "select", "insert", "delete", "drop",
            "admin", "root", "password", "login"
        ]
        
        url_lower = url.lower()
        for pattern in suspicious_patterns:
            if pattern in url_lower:
                logger.warning(
                    f"Suspicious request detected: {pattern} in URL - "
                    f"IP: {client_ip} - "
                    f"URL: {url} - "
                    f"User-Agent: {user_agent}"
                )
                break
        
        # Check for missing or suspicious user agent
        if not user_agent or len(user_agent) < 10:
            logger.warning(
                f"Suspicious User-Agent: {user_agent} - "
                f"IP: {client_ip} - "
                f"URL: {url}"
            )
        
        return await call_next(request)
