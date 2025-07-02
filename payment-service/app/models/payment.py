from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, Text

from app.db.database import Base


class PaymentStatus(str, PyEnum):
    """
    Payment status enum
    """
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(str, PyEnum):
    """
    Payment method enum
    """
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    PAYPAL = "paypal"
    CRYPTO = "crypto"
    OTHER = "other"


class Payment(Base):
    """
    Payment model
    """
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), index=True, nullable=False)
    invoice_id = Column(Integer, index=True)
    invoice_number = Column(String(20), index=True)
    
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    payment_method_details = Column(Text, nullable=True)  # JSON string with details
    
    transaction_reference = Column(String(255), nullable=True, unique=True, index=True)
    external_reference = Column(String(255), nullable=True)  # External payment gateway reference
    
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    status_message = Column(Text, nullable=True)
    
    payment_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PaymentAttempt(Base):
    """
    Payment attempt model
    
    Records attempts to process payments, including failures,
    for audit and debugging purposes.
    """
    __tablename__ = "payment_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, index=True)
    
    gateway_request = Column(Text, nullable=True)  # JSON string with request details
    gateway_response = Column(Text, nullable=True)  # JSON string with response details
    
    success = Column(Integer, default=0)  # 0=false, 1=true
    error_message = Column(Text, nullable=True)
    
    correlation_id = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
