import os
from typing import Any, Dict, Optional, List

from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Invoice Service"
    API_V1_STR: str = "/api/v1"
    
    # Server settings
    PORT: int = 8003
    
    # Security
    JWT_PUBLIC_KEY: str = os.getenv("JWT_PUBLIC_KEY", "shared-public-key-for-development")
    JWT_ALGORITHM: str = "HS256"
    
    # Database
    DATABASE_URL: Optional[PostgresDsn] = os.getenv("INVOICE_SERVICE_DATABASE_URL")
    
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
            path=f"/{os.getenv('INVOICE_SERVICE_POSTGRES_DB', 'invoice_service_db')}",
        )
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # RabbitMQ
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
    
    # Service URLs
    TAX_SERVICE_URL: str = os.getenv("TAX_SERVICE_URL", "http://tax-service:8001/api/v1")
    DISCOUNT_SERVICE_URL: str = os.getenv("DISCOUNT_SERVICE_URL", "http://discount-service:8002/api/v1")
    PAYMENT_SERVICE_URL: str = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8004/api/v1")
    
    # PDF Generation
    PDF_GENERATION_ENABLED: bool = os.getenv("PDF_GENERATION_ENABLED", "true").lower() == "true"
    PDF_STORAGE_PATH: str = os.getenv("PDF_STORAGE_PATH", "/app/pdf_storage")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
