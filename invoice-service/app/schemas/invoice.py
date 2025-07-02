from datetime import datetime
from typing import List, Optional
from decimal import Decimal

from pydantic import BaseModel, Field, EmailStr


class InvoiceItemCreate(BaseModel):
    """Schema for creating an invoice item"""
    description: str
    quantity: Decimal
    unit_price: Decimal


class InvoiceItemResponse(BaseModel):
    """Schema for invoice item response"""
    id: int
    description: str
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal
    
    class Config:
        from_attributes = True


class InvoiceCreate(BaseModel):
    """Schema for creating an invoice"""
    customer_id: str
    customer_name: str
    customer_email: EmailStr
    customer_address: Optional[str] = None
    subtotal: Decimal
    tax_amount: Optional[Decimal] = Field(default=0)
    discount_amount: Optional[Decimal] = Field(default=0)
    notes: Optional[str] = None
    due_date: Optional[datetime] = None
    items: List[InvoiceItemCreate]


class InvoiceResponse(BaseModel):
    """Schema for invoice response"""
    id: int
    invoice_number: str
    customer_id: str
    customer_name: str
    customer_email: str
    customer_address: Optional[str] = None
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    status: str
    notes: Optional[str] = None
    issue_date: datetime
    due_date: Optional[datetime] = None
    paid_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    items: List[InvoiceItemResponse]
    
    class Config:
        from_attributes = True


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice"""
    customer_name: Optional[str] = None
    customer_email: Optional[EmailStr] = None
    customer_address: Optional[str] = None
    notes: Optional[str] = None
    due_date: Optional[datetime] = None


class InvoicePaymentResponse(BaseModel):
    """Schema for invoice payment response"""
    id: int
    payment_id: str
    amount: Decimal
    payment_date: datetime
    payment_method: str
    transaction_reference: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class InvoiceStatusUpdate(BaseModel):
    """Schema for updating invoice status"""
    status: str


class InvoiceCreatedEvent(BaseModel):
    """Schema for invoice created event"""
    event_id: str
    event_type: str = "invoice_created"
    timestamp: str
    correlation_id: str
    payload: dict


class InvoiceUpdatedEvent(BaseModel):
    """Schema for invoice updated event"""
    event_id: str
    event_type: str = "invoice_updated"
    timestamp: str
    correlation_id: str
    payload: dict
