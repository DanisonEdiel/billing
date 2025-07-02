import json
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from loguru import logger

from app.models.payment import PaymentStatus, PaymentMethod
from app.repositories.payment_repository import payment_repository
from app.core.event_publisher import event_publisher
from app.core.config import settings


class MockPaymentGateway:
    """
    Mock payment gateway for development and testing purposes
    """
    
    async def process_payment(
        self, 
        amount: float,
        currency: str,
        payment_method: str,
        payment_details: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a payment through the mock gateway"""
        # Simulate payment processing
        # In a real implementation, this would make an API call to a payment provider
        
        # Simulate card declined for testing purposes
        if payment_details.get("card_number", "").endswith("0000"):
            return {
                "success": False,
                "error_code": "card_declined",
                "error_message": "Card was declined",
                "transaction_id": None
            }
        
        # Otherwise, simulate success
        return {
            "success": True,
            "transaction_id": f"mock-txn-{datetime.utcnow().timestamp()}",
            "status": "completed",
            "details": {
                "amount": amount,
                "currency": currency,
                "payment_method": payment_method
            }
        }


class PaymentGateway:
    """
    Integration with a real payment gateway
    """
    
    async def process_payment(
        self, 
        amount: float,
        currency: str,
        payment_method: str,
        payment_details: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a payment through the payment gateway"""
        try:
            # In a real implementation, this would make an API call to a payment provider
            # like Stripe, PayPal, etc.
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.PAYMENT_GATEWAY_BASE_URL}/v1/payments",
                    json={
                        "amount": amount,
                        "currency": currency,
                        "payment_method": payment_method,
                        "payment_details": payment_details,
                        "metadata": metadata
                    },
                    headers={
                        "Authorization": f"Bearer {settings.PAYMENT_GATEWAY_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    timeout=30.0
                )
                
                data = response.json()
                
                if response.status_code >= 400:
                    return {
                        "success": False,
                        "error_code": data.get("error", {}).get("code"),
                        "error_message": data.get("error", {}).get("message"),
                        "transaction_id": None
                    }
                
                return {
                    "success": True,
                    "transaction_id": data.get("id"),
                    "status": data.get("status"),
                    "details": data
                }
                
        except Exception as e:
            logger.error(f"Payment gateway error: {str(e)}")
            return {
                "success": False,
                "error_code": "gateway_error",
                "error_message": str(e),
                "transaction_id": None
            }


class PaymentService:
    """
    Service layer for payment operations - contains business logic
    """
    
    def __init__(self):
        """Initialize payment service with appropriate gateway"""
        if settings.USE_MOCK_PAYMENT_GATEWAY:
            self.payment_gateway = MockPaymentGateway()
        else:
            self.payment_gateway = PaymentGateway()
    
    async def create_payment(
        self,
        db: Session,
        user_id: str,
        invoice_id: int,
        invoice_number: str,
        amount: Decimal,
        payment_method: str,
        payment_details: Dict[str, Any],
        correlation_id: str = None
    ):
        """
        Create and process a payment
        
        This method creates a payment record, processes it through the
        payment gateway, and publishes events based on the outcome.
        """
        # Validate payment method
        if payment_method not in [method.value for method in PaymentMethod]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid payment method: {payment_method}"
            )
        
        # Create payment record
        db_payment = payment_repository.create_payment(
            db=db,
            user_id=user_id,
            invoice_id=invoice_id,
            invoice_number=invoice_number,
            amount=float(amount),
            currency="USD",  # Default currency
            payment_method=payment_method,
            payment_method_details=payment_details,
            status=PaymentStatus.PROCESSING,
            correlation_id=correlation_id
        )
        
        # Process payment through gateway
        gateway_response = await self.payment_gateway.process_payment(
            amount=float(amount),
            currency="USD",
            payment_method=payment_method,
            payment_details=payment_details,
            metadata={
                "user_id": user_id,
                "invoice_id": invoice_id,
                "invoice_number": invoice_number,
                "payment_id": db_payment.id,
                "correlation_id": correlation_id
            }
        )
        
        # Record payment attempt
        payment_repository.record_payment_attempt(
            db=db,
            payment_id=db_payment.id,
            gateway_request={
                "amount": float(amount),
                "currency": "USD",
                "payment_method": payment_method,
                "metadata": {
                    "invoice_id": invoice_id,
                    "invoice_number": invoice_number
                }
            },
            gateway_response=gateway_response,
            success=gateway_response.get("success", False),
            error_message=gateway_response.get("error_message"),
            correlation_id=correlation_id
        )
        
        # Update payment based on gateway response
        if gateway_response.get("success"):
            updated_payment = payment_repository.update_payment_status(
                db=db,
                payment=db_payment,
                status=PaymentStatus.COMPLETED,
                external_reference=gateway_response.get("transaction_id")
            )
            
            # Publish payment received event
            await event_publisher.publish_payment_received(
                payment_data={
                    "id": updated_payment.id,
                    "invoice_id": updated_payment.invoice_id,
                    "invoice_number": updated_payment.invoice_number,
                    "amount": updated_payment.amount,
                    "payment_method": updated_payment.payment_method,
                    "transaction_reference": updated_payment.transaction_reference,
                    "payment_date": updated_payment.payment_date.isoformat() if updated_payment.payment_date else datetime.utcnow().isoformat(),
                    "status": updated_payment.status,
                    "user_id": user_id
                },
                correlation_id=correlation_id
            )
        else:
            updated_payment = payment_repository.update_payment_status(
                db=db,
                payment=db_payment,
                status=PaymentStatus.FAILED,
                status_message=gateway_response.get("error_message")
            )
            
            # Publish payment failed event
            await event_publisher.publish_payment_failed(
                payment_data={
                    "id": updated_payment.id,
                    "invoice_id": updated_payment.invoice_id,
                    "invoice_number": updated_payment.invoice_number,
                    "amount": updated_payment.amount,
                    "payment_method": updated_payment.payment_method,
                    "error_message": gateway_response.get("error_message"),
                    "user_id": user_id
                },
                correlation_id=correlation_id
            )
        
        return updated_payment
    
    def get_payment(self, db: Session, payment_id: int, user_id: str):
        """Get a payment by ID"""
        payment = payment_repository.get_payment_by_id(db, payment_id)
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment with ID {payment_id} not found"
            )
            
        # Check if user has access to this payment
        if payment.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this payment"
            )
        
        # Parse JSON payment method details if present
        if payment.payment_method_details:
            try:
                payment.payment_method_details = json.loads(payment.payment_method_details)
            except json.JSONDecodeError:
                payment.payment_method_details = {}
            
        return payment
    
    def get_user_payments(
        self,
        db: Session,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ):
        """Get all payments for a user"""
        payments = payment_repository.get_payments_by_user(db, user_id, skip, limit)
        
        # Parse JSON payment method details for each payment
        for payment in payments:
            if payment.payment_method_details:
                try:
                    payment.payment_method_details = json.loads(payment.payment_method_details)
                except json.JSONDecodeError:
                    payment.payment_method_details = {}
        
        return payments
    
    def get_invoice_payments(
        self,
        db: Session,
        invoice_id: int,
        user_id: str
    ):
        """Get all payments for an invoice"""
        payments = payment_repository.get_payments_by_invoice_id(db, invoice_id)
        
        # Filter by user_id for security
        payments = [p for p in payments if p.user_id == user_id]
        
        # Parse JSON payment method details for each payment
        for payment in payments:
            if payment.payment_method_details:
                try:
                    payment.payment_method_details = json.loads(payment.payment_method_details)
                except json.JSONDecodeError:
                    payment.payment_method_details = {}
        
        return payments
    
    async def handle_webhook_event(
        self,
        db: Session,
        event_data: Dict[str, Any]
    ):
        """
        Handle webhook events from payment gateway
        
        This method processes webhook notifications from the payment gateway,
        updates payment records accordingly, and publishes events.
        """
        event_type = event_data.get("event_type")
        transaction_id = event_data.get("transaction_id")
        
        if not transaction_id:
            logger.error(f"Webhook event missing transaction_id: {event_data}")
            return {"status": "error", "message": "Missing transaction_id"}
        
        # Find payment by external_reference
        payment = payment_repository.get_payment_by_transaction_reference(db, transaction_id)
        
        if not payment:
            logger.error(f"Payment not found for transaction_id: {transaction_id}")
            return {"status": "error", "message": "Payment not found"}
        
        # Handle different event types
        if event_type == "payment.succeeded":
            payment_repository.update_payment_status(
                db=db,
                payment=payment,
                status=PaymentStatus.COMPLETED,
                status_message="Payment confirmed by gateway"
            )
            
            # Publish payment received event
            await event_publisher.publish_payment_received(
                payment_data={
                    "id": payment.id,
                    "invoice_id": payment.invoice_id,
                    "invoice_number": payment.invoice_number,
                    "amount": payment.amount,
                    "payment_method": payment.payment_method,
                    "transaction_reference": payment.transaction_reference,
                    "payment_date": payment.payment_date.isoformat() if payment.payment_date else datetime.utcnow().isoformat(),
                    "status": payment.status,
                    "user_id": payment.user_id
                }
            )
            
        elif event_type == "payment.failed":
            payment_repository.update_payment_status(
                db=db,
                payment=payment,
                status=PaymentStatus.FAILED,
                status_message=event_data.get("error_message", "Payment failed")
            )
            
            # Publish payment failed event
            await event_publisher.publish_payment_failed(
                payment_data={
                    "id": payment.id,
                    "invoice_id": payment.invoice_id,
                    "invoice_number": payment.invoice_number,
                    "amount": payment.amount,
                    "payment_method": payment.payment_method,
                    "error_message": event_data.get("error_message", "Payment failed"),
                    "user_id": payment.user_id
                }
            )
            
        elif event_type == "payment.refunded":
            payment_repository.update_payment_status(
                db=db,
                payment=payment,
                status=PaymentStatus.REFUNDED,
                status_message="Payment refunded"
            )
            
        return {"status": "success"}


async def handle_invoice_created(event):
    """
    Handle invoice_created event
    
    This function is called when an invoice_created event is consumed.
    It could be used to automatically process payments for invoices if needed.
    For now, it just logs the event.
    """
    logger.info(f"Handling invoice_created event: {event.get('event_id')}")
    
    # In a production system, this might automatically process payments
    # for certain customers with auto-pay enabled, or send payment reminders.


# Singleton instance
payment_service = PaymentService()
