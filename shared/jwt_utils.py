import jwt
from fastapi import Request, HTTPException, status
from pydantic import BaseModel


class JWTConfig(BaseModel):
    """JWT configuration settings"""
    public_key: str
    algorithm: str = "RS256"


async def jwt_middleware_factory(config: JWTConfig):
    """
    Create a JWT middleware with the specified configuration
    
    Args:
        config: JWT configuration settings
        
    Returns:
        A middleware function to be used with FastAPI
    """
    async def jwt_middleware(request: Request, call_next):
        """
        Middleware to validate JWT token and extract user_id
        
        This middleware checks for the Authorization header with a Bearer token,
        validates it against the provided JWT_PUBLIC_KEY, and extracts the user_id
        for use in subsequent request handling.
        """
        # Skip auth for health check and docs endpoints
        if request.url.path.endswith("/health") or request.url.path.endswith("/docs") or \
           request.url.path.endswith("/openapi.json") or request.url.path.endswith("/redoc") or \
           request.url.path.startswith("/webhook"):  # Skip auth for webhook endpoints
            return await call_next(request)
        
        authorization = request.headers.get("Authorization")
        
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing",
            )
        
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme",
                )
            
            payload = jwt.decode(
                token,
                config.public_key,
                algorithms=[config.algorithm]
            )
            
            user_id = payload.get("user_id")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                )
            
            # Add user_id to request state for use in route handlers
            request.state.user_id = user_id
        except (jwt.PyJWTError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        
        return await call_next(request)
    
    return jwt_middleware
