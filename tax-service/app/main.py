import time
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.api.routes import tax_routes
from app.core.config import settings
from app.core.event_publisher import event_publisher
from app.core.jwt_auth import jwt_middleware

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)l

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add JWT middleware
app.middleware("http")(jwt_middleware)

# Include routers
app.include_router(tax_routes.router, prefix=settings.API_V1_STR)


# Set up correlation ID and logging middleware
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid4())
    request.state.correlation_id = correlation_id
    
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    response.headers["X-Correlation-ID"] = correlation_id
    
    # Log request details with correlation ID
    print(f"[{correlation_id}] Request: {request.method} {request.url.path} | Status: {response.status_code} | Time: {process_time:.4f}s")
    
    return response


@app.on_event("startup")
async def startup_event():
    # Connect to message broker
    await event_publisher.connect()
    print("Tax Service started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    # Disconnect from message broker
    await event_publisher.disconnect()
    print("Tax Service shutdown successfully")


# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        description="Tax calculation service API for the Billing domain",
        routes=app.routes,
    )
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
