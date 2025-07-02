import jwt
from fastapi import Request, HTTPException, status
from app.core.config import settings


async def jwt_middleware(request: Request, call_next):
    """
    Middleware to validate JWT token and extract user_id
    
    This middleware checks for the Authorization header with a Bearer token,
    validates it against the JWT_PUBLIC_KEY, and extracts the user_id
    for use in subsequent request handling.
    """
    # Skip auth for health check and docs endpoints
    if request.url.path.endswith("/health") or request.url.path.endswith("/docs") or \
       request.url.path.endswith("/openapi.json") or request.url.path.endswith("/redoc") or \
       request.url.path.endswith("/webhook"):  # Skip auth for payment webhook endpoints
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
            settings.JWT_PUBLIC_KEY,
            algorithms=[settings.JWT_ALGORITHM]
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
