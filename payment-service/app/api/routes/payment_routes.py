from typing import List, Optional

from fastapi import APIRouter, Depends, Request, Body
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.payment import (
    PaymentCreate,
    PaymentResponse,
    PaymentStatusUpdate,
    PaymentInitiateRequest,
    PaymentInitiateResponse,
    PaymentWebhookEvent
)
from app.services.payment_service import payment_service


router = APIRouter()


@router.post("/payments", response_model=PaymentResponse, status_code=201)
async def create_payment(
    request: Request,
    payment_data: PaymentCreate,
    db: Session = Depends(get_db)
):
    """
    Create and process a new payment
    """
    user_id = request.state.user_id
    correlation_id = getattr(request.state, "correlation_id", None)
    
    return await payment_service.create_payment(
        db=db,
        user_id=user_id,
        invoice_id=payment_data.invoice_id,
        invoice_number=payment_data.invoice_number,
        amount=payment_data.amount,
        payment_method=payment_data.payment_method,
        payment_details=payment_data.payment_method_details,
        correlation_id=correlation_id
    )


@router.post("/payments/initiate", response_model=PaymentInitiateResponse)
async def initiate_payment(
    request: Request,
    payment_data: PaymentInitiateRequest,
    db: Session = Depends(get_db)
):
    """
    Initiate a payment (for payment flows that require redirection)
    
    This endpoint would be used when a payment requires a redirect flow,
    such as for 3D Secure authentication or PayPal checkout.
    """
    user_id = request.state.user_id
    correlation_id = getattr(request.state, "correlation_id", None)
    
    # In a real implementation, this would initiate a payment and return
    # details like a checkout URL. For now, we'll simulate this by creating
    # a regular payment.
    payment = await payment_service.create_payment(
        db=db,
        user_id=user_id,
        invoice_id=payment_data.invoice_id,
        invoice_number=f"INV-{payment_data.invoice_id}",  # Simulated
        amount=100.00,  # Simulated amount
        payment_method=payment_data.payment_method,
        payment_details=payment_data.payment_method_details,
        correlation_id=correlation_id
    )
    
    return PaymentInitiateResponse(
        payment_id=payment.id,
        checkout_url=f"https://example.com/checkout/{payment.id}" if payment_data.return_url else None,
        status=payment.status,
        transaction_reference=payment.transaction_reference
    )


@router.get("/payments", response_model=List[PaymentResponse])
async def get_payments(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    invoice_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get all payments for the current user, optionally filtered by invoice_id
    """
    user_id = request.state.user_id
    
    if invoice_id:
        return payment_service.get_invoice_payments(
            db=db, 
            invoice_id=invoice_id, 
            user_id=user_id
        )
    
    return payment_service.get_user_payments(
        db=db,
        user_id=user_id,
        skip=skip,
        limit=limit
    )


@router.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    request: Request,
    payment_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific payment by ID
    """
    user_id = request.state.user_id
    return payment_service.get_payment(db=db, payment_id=payment_id, user_id=user_id)


@router.post("/webhook", status_code=200)
async def payment_webhook(
    event: PaymentWebhookEvent,
    db: Session = Depends(get_db)
):
    """
    Handle webhook events from payment gateway
    
    This endpoint receives webhook notifications from the payment gateway
    and processes them accordingly.
    """
    # Process the webhook event
    return await payment_service.handle_webhook_event(db=db, event_data=event.model_dump())


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "ok"}
