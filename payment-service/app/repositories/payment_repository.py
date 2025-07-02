import json
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.payment import Payment, PaymentAttempt, PaymentStatus


class PaymentRepository:
    """
    Repository for payment operations, follows the repository pattern
    to abstract database operations
    """
    
    def create_payment(
        self,
        db: Session,
        user_id: str,
        invoice_id: int,
        invoice_number: str,
        amount: float,
        currency: str,
        payment_method: str,
        payment_method_details: Dict[str, Any] = None,
        status: PaymentStatus = PaymentStatus.PENDING,
        correlation_id: Optional[str] = None
    ) -> Payment:
        """Create a new payment"""
        db_payment = Payment(
            user_id=user_id,
            invoice_id=invoice_id,
            invoice_number=invoice_number,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            payment_method_details=json.dumps(payment_method_details) if payment_method_details else None,
            status=status,
            transaction_reference=f"TXN-{int(datetime.utcnow().timestamp())}-{invoice_id}"
        )
        db.add(db_payment)
        db.commit()
        db.refresh(db_payment)
        return db_payment
    
    def get_payment_by_id(self, db: Session, payment_id: int) -> Optional[Payment]:
        """Get a payment by ID"""
        return db.query(Payment).filter(Payment.id == payment_id).first()
    
    def get_payment_by_transaction_reference(self, db: Session, transaction_reference: str) -> Optional[Payment]:
        """Get a payment by transaction reference"""
        return db.query(Payment).filter(Payment.transaction_reference == transaction_reference).first()
    
    def get_payments_by_invoice_id(self, db: Session, invoice_id: int) -> List[Payment]:
        """Get all payments for an invoice"""
        return db.query(Payment).filter(Payment.invoice_id == invoice_id).all()
    
    def get_payments_by_user(
        self,
        db: Session,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Payment]:
        """Get all payments for a user"""
        return db.query(Payment).filter(
            Payment.user_id == user_id
        ).order_by(desc(Payment.created_at)).offset(skip).limit(limit).all()
    
    def update_payment(
        self,
        db: Session,
        payment: Payment,
        update_data: Dict[str, Any]
    ) -> Payment:
        """Update a payment"""
        for key, value in update_data.items():
            if hasattr(payment, key):
                if key == "payment_method_details" and value:
                    setattr(payment, key, json.dumps(value))
                else:
                    setattr(payment, key, value)
        
        payment.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(payment)
        return payment
    
    def update_payment_status(
        self,
        db: Session,
        payment: Payment,
        status: PaymentStatus,
        status_message: Optional[str] = None,
        external_reference: Optional[str] = None
    ) -> Payment:
        """Update a payment status"""
        payment.status = status
        if status_message:
            payment.status_message = status_message
        if external_reference:
            payment.external_reference = external_reference
        
        # If payment is completed, record the payment date
        if status == PaymentStatus.COMPLETED and not payment.payment_date:
            payment.payment_date = datetime.utcnow()
        
        payment.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(payment)
        return payment
    
    def record_payment_attempt(
        self,
        db: Session,
        payment_id: int,
        gateway_request: Dict[str, Any],
        gateway_response: Dict[str, Any],
        success: bool,
        error_message: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> PaymentAttempt:
        """Record a payment attempt"""
        db_attempt = PaymentAttempt(
            payment_id=payment_id,
            gateway_request=json.dumps(gateway_request),
            gateway_response=json.dumps(gateway_response),
            success=1 if success else 0,
            error_message=error_message,
            correlation_id=correlation_id
        )
        db.add(db_attempt)
        db.commit()
        db.refresh(db_attempt)
        return db_attempt
    
    def get_payment_attempts(
        self,
        db: Session,
        payment_id: int
    ) -> List[PaymentAttempt]:
        """Get all payment attempts for a payment"""
        return db.query(PaymentAttempt).filter(
            PaymentAttempt.payment_id == payment_id
        ).order_by(PaymentAttempt.created_at.desc()).all()


# Singleton instance
payment_repository = PaymentRepository()
