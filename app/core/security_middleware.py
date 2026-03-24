import logging
import time
from typing import Dict, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis
from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis."""
    
    def __init__(self, app, redis_url: str = None):
        super().__init__(app)
        self.redis_url = redis_url or settings.REDIS_URL
        self.redis_client: Optional[redis.Redis] = None
    
    async def get_redis_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self.redis_client is None:
            self.redis_client = redis.from_url(
                self.redis_url, 
                decode_responses=True,
                retry_on_error=[ConnectionError, TimeoutError]
            )
        return self.redis_client
    
    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting based on IP address."""
        client_ip = self.get_client_ip(request)
        
        # Skip rate limiting for health checks and docs
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        try:
            redis_client = await self.get_redis_client()
            
            # Create rate limit key
            rate_limit_key = f"rate_limit:{client_ip}"
            
            # Get current count
            current_requests = await redis_client.get(rate_limit_key)
            
            if current_requests is None:
                # First request from this IP
                await redis_client.setex(rate_limit_key, 60, 1)
                current_requests = 1
            else:
                current_requests = int(current_requests)
                
                if current_requests >= settings.RATE_LIMIT_PER_MINUTE:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded. Try again later.",
                        headers={"Retry-After": "60"}
                    )
                
                # Increment counter
                await redis_client.incr(rate_limit_key)
                current_requests += 1
            
            # Add rate limit headers to response
            response = await call_next(request)
            response.headers["X-Rate-Limit-Limit"] = str(settings.RATE_LIMIT_PER_MINUTE)
            response.headers["X-Rate-Limit-Remaining"] = str(
                max(0, settings.RATE_LIMIT_PER_MINUTE - current_requests)
            )
            response.headers["X-Rate-Limit-Reset"] = str(int(time.time()) + 60)
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            # If Redis is down, log error but don't block requests
            logger.warning(f"Rate limiting error: {e}")
            return await call_next(request)
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check for forwarded headers (for load balancers)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )
        
        # Content Security Policy (adjust based on your needs)
        if not settings.DEBUG:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            )
        
        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validate and sanitize incoming requests."""
    
    # Maximum request size (10MB)
    MAX_REQUEST_SIZE = 10 * 1024 * 1024
    
    # Blocked user agents (basic bot protection)
    BLOCKED_USER_AGENTS = [
        "sqlmap",
        "nikto",
        "nmap",
        "masscan",
        "nessus",
        "openvas",
        "w3af",
        "dirbuster",
        "gobuster",
    ]
    
    async def dispatch(self, request: Request, call_next):
        # Check user agent
        user_agent = request.headers.get("user-agent", "").lower()
        for blocked_agent in self.BLOCKED_USER_AGENTS:
            if blocked_agent in user_agent:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Blocked user agent"
                )
        
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_REQUEST_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Request entity too large"
            )
        
        # Check for suspicious paths
        suspicious_patterns = [
            "/.env",
            "/wp-admin",
            "/admin.php",
            "/phpmyadmin",
            "/.git",
            "/config",
            "/backup",
            "/database",
            "/.aws",
            "/.ssh",
        ]
        
        path = request.url.path.lower()
        for pattern in suspicious_patterns:
            if pattern in path:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Not found"
                )
        
        return await call_next(request)


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Optional API key middleware for additional protection."""
    
    def __init__(self, app, required_endpoints: list = None):
        super().__init__(app)
        self.required_endpoints = required_endpoints or []
    
    async def dispatch(self, request: Request, call_next):
        # Skip if endpoint doesn't require API key
        if not any(endpoint in request.url.path for endpoint in self.required_endpoints):
            return await call_next(request)
        
        # Check for API key in headers
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required",
                headers={"WWW-Authenticate": "ApiKey"}
            )
        
        # Validate API key (implement your own logic)
        if not self.validate_api_key(api_key):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        return await call_next(request)
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key - implement your own logic."""
        # This is a placeholder - implement proper API key validation
        valid_keys = getattr(settings, "VALID_API_KEYS", [])
        return api_key in valid_keys


# Request logging for audit trails
class AuditLogMiddleware(BaseHTTPMiddleware):
    """Log requests for security auditing."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Get request info
        client_ip = self.get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log request (you can send this to your logging system)
        log_data = {
            "timestamp": int(time.time()),
            "method": request.method,
            "path": str(request.url.path),
            "query_params": str(request.query_params),
            "client_ip": client_ip,
            "user_agent": user_agent,
            "status_code": response.status_code,
            "process_time": round(process_time, 3),
        }
        
        # Log to console (replace with proper logging)
        if response.status_code >= 400:
            logger.warning(f"Security audit: {log_data}")
        
        return response
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
