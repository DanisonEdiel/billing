from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal

from pydantic import BaseModel, Field


class PaymentMethodDetails(BaseModel):
    """Base schema for payment method details"""
    type: str


class CreditCardDetails(PaymentMethodDetails):
    """Credit card payment method details"""
    type: str = "credit_card"
    last_four: str
    brand: str
    exp_month: int
    exp_year: int


class BankTransferDetails(PaymentMethodDetails):
    """Bank transfer payment method details"""
    type: str = "bank_transfer"
    bank_name: str
    account_last_four: str


class PaymentCreate(BaseModel):
    """Schema for creating a payment"""
    invoice_id: int
    invoice_number: str
    amount: Decimal
    currency: str = "USD"
    payment_method: str
    payment_method_details: Dict[str, Any]


class PaymentResponse(BaseModel):
    """Schema for payment response"""
    id: int
    user_id: str
    invoice_id: int
    invoice_number: str
    amount: Decimal
    currency: str
    payment_method: str
    payment_method_details: Optional[Dict[str, Any]] = None
    transaction_reference: Optional[str] = None
    external_reference: Optional[str] = None
    status: str
    status_message: Optional[str] = None
    payment_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PaymentStatusUpdate(BaseModel):
    """Schema for updating payment status"""
    status: str
    status_message: Optional[str] = None


class PaymentWebhookEvent(BaseModel):
    """Schema for payment webhook events from payment gateway"""
    event_type: str
    transaction_id: str
    amount: Decimal
    status: str
    metadata: Optional[Dict[str, Any]] = None


class PaymentInitiateRequest(BaseModel):
    """Schema for initiating a payment"""
    invoice_id: int
    payment_method: str
    payment_method_details: Dict[str, Any] = Field(..., 
        description="Payment method details specific to the payment method")
    return_url: Optional[str] = None


class PaymentInitiateResponse(BaseModel):
    """Schema for payment initiation response"""
    payment_id: int
    checkout_url: Optional[str] = None
    status: str
    transaction_reference: str


class PaymentReceivedEvent(BaseModel):
    """Schema for payment received event"""
    event_id: str
    event_type: str = "payment_received"
    timestamp: str
    correlation_id: str
    payload: dict


class PaymentFailedEvent(BaseModel):
    """Schema for payment failed event"""
    event_id: str
    event_type: str = "payment_failed"
    timestamp: str
    correlation_id: str
    payload: dict
