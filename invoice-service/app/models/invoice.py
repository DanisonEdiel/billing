from datetime import datetime
from enum import Enum as PyEnum
from typing import List

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, Text
from sqlalchemy.orm import relationship

from app.db.database import Base


class InvoiceStatus(str, PyEnum):
    """
    Invoice status enum
    """
    DRAFT = "draft"
    ISSUED = "issued"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class Invoice(Base):
    """
    Invoice model
    """
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(20), unique=True, index=True)
    user_id = Column(String(255), index=True, nullable=False)
    customer_id = Column(String(255), index=True)
    customer_name = Column(String(255))
    customer_email = Column(String(255))
    customer_address = Column(Text)
    
    subtotal = Column(Float, nullable=False)
    tax_amount = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    notes = Column(Text, nullable=True)
    
    issue_date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=True)
    paid_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with InvoiceItem
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    
    # Relationship with InvoicePayment
    payments = relationship("InvoicePayment", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceItem(Base):
    """
    Invoice line item model
    """
    __tablename__ = "invoice_items"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    
    description = Column(String(255), nullable=False)
    quantity = Column(Float, nullable=False, default=1.0)
    unit_price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)  # quantity * unit_price
    
    # Relationship with Invoice
    invoice = relationship("Invoice", back_populates="items")


class InvoicePayment(Base):
    """
    Invoice payment model
    """
    __tablename__ = "invoice_payments"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    
    payment_id = Column(String(255), nullable=False, index=True)  # External payment ID from payment service
    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime, default=datetime.utcnow)
    payment_method = Column(String(50))
    transaction_reference = Column(String(255))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship with Invoice
    invoice = relationship("Invoice", back_populates="payments")


class InvoiceHistory(Base):
    """
    Invoice history log model
    """
    __tablename__ = "invoice_history"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    
    user_id = Column(String(255), nullable=True)
    action = Column(String(50), nullable=False)  # created, updated, status_change, etc.
    details = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
