import os
from typing import Any, Dict, Optional, List

from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Payment Service"
    API_V1_STR: str = "/api/v1"
    
    # Server settings
    PORT: int = 8004
    
    # Security
    JWT_PUBLIC_KEY: str = os.getenv("JWT_PUBLIC_KEY", "shared-public-key-for-development")
    JWT_ALGORITHM: str = "HS256"
    
    # Database
    DATABASE_URL: Optional[PostgresDsn] = os.getenv("PAYMENT_SERVICE_DATABASE_URL")
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            username=os.getenv("POSTGRES_USER", "billing_user"),
            password=os.getenv("POSTGRES_PASSWORD", "secret"),
            host=os.getenv("POSTGRES_HOST", "postgres"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            path=f"/{os.getenv('PAYMENT_SERVICE_POSTGRES_DB', 'payment_service_db')}",
        )
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # RabbitMQ
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
    
    # Service URLs
    INVOICE_SERVICE_URL: str = os.getenv("INVOICE_SERVICE_URL", "http://invoice-service:8003/api/v1")
    
    # Payment Gateway Integration
    PAYMENT_GATEWAY_API_KEY: str = os.getenv("PAYMENT_GATEWAY_API_KEY", "test_api_key")
    PAYMENT_GATEWAY_SECRET: str = os.getenv("PAYMENT_GATEWAY_SECRET", "test_secret")
    PAYMENT_GATEWAY_BASE_URL: str = os.getenv("PAYMENT_GATEWAY_BASE_URL", "https://api.payment-gateway.example")
    PAYMENT_GATEWAY_WEBHOOK_SECRET: str = os.getenv("PAYMENT_GATEWAY_WEBHOOK_SECRET", "test_webhook_secret")
    
    # Mock payment gateway for development
    USE_MOCK_PAYMENT_GATEWAY: bool = os.getenv("USE_MOCK_PAYMENT_GATEWAY", "true").lower() == "true"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
