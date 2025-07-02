from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceResponse,
    InvoiceUpdate,
    InvoiceStatusUpdate,
    InvoicePaymentResponse
)
from app.services.invoice_service import invoice_service


router = APIRouter()


@router.post("/invoices", response_model=InvoiceResponse, status_code=201)
async def create_invoice(
    request: Request,
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new invoice
    """
    user_id = request.state.user_id
    correlation_id = getattr(request.state, "correlation_id", None)
    
    return await invoice_service.create_invoice(
        db=db,
        user_id=user_id,
        customer_id=invoice_data.customer_id,
        customer_name=invoice_data.customer_name,
        customer_email=invoice_data.customer_email,
        customer_address=invoice_data.customer_address,
        subtotal=invoice_data.subtotal,
        tax_amount=invoice_data.tax_amount,
        discount_amount=invoice_data.discount_amount,
        items=invoice_data.items,
        notes=invoice_data.notes,
        due_date=invoice_data.due_date,
        correlation_id=correlation_id
    )


@router.get("/invoices", response_model=List[InvoiceResponse])
async def get_invoices(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    customer_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all invoices for the current user, optionally filtered by customer_id
    """
    user_id = request.state.user_id
    
    if customer_id:
        return invoice_service.get_customer_invoices(
            db=db, 
            user_id=user_id, 
            customer_id=customer_id, 
            skip=skip, 
            limit=limit
        )
    
    return invoice_service.get_user_invoices(
        db=db,
        user_id=user_id,
        skip=skip,
        limit=limit
    )


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    request: Request,
    invoice_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific invoice by ID
    """
    user_id = request.state.user_id
    return invoice_service.get_invoice(db=db, invoice_id=invoice_id, user_id=user_id)


@router.put("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    request: Request,
    invoice_id: int,
    invoice_data: InvoiceUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an invoice
    """
    user_id = request.state.user_id
    correlation_id = getattr(request.state, "correlation_id", None)
    
    return await invoice_service.update_invoice(
        db=db,
        invoice_id=invoice_id,
        user_id=user_id,
        update_data=invoice_data.model_dump(exclude_unset=True),
        correlation_id=correlation_id
    )


@router.post("/invoices/{invoice_id}/issue", response_model=InvoiceResponse)
async def issue_invoice(
    request: Request,
    invoice_id: int,
    db: Session = Depends(get_db)
):
    """
    Issue an invoice (change status from DRAFT to ISSUED)
    """
    user_id = request.state.user_id
    correlation_id = getattr(request.state, "correlation_id", None)
    
    return await invoice_service.issue_invoice(
        db=db,
        invoice_id=invoice_id,
        user_id=user_id,
        correlation_id=correlation_id
    )


@router.post("/invoices/{invoice_id}/cancel", response_model=InvoiceResponse)
async def cancel_invoice(
    request: Request,
    invoice_id: int,
    db: Session = Depends(get_db)
):
    """
    Cancel an invoice
    """
    user_id = request.state.user_id
    correlation_id = getattr(request.state, "correlation_id", None)
    
    return await invoice_service.cancel_invoice(
        db=db,
        invoice_id=invoice_id,
        user_id=user_id,
        correlation_id=correlation_id
    )


@router.get("/invoices/{invoice_id}/payments", response_model=List[InvoicePaymentResponse])
async def get_invoice_payments(
    request: Request,
    invoice_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all payments for an invoice
    """
    user_id = request.state.user_id
    return invoice_service.get_invoice_payments(
        db=db,
        invoice_id=invoice_id,
        user_id=user_id
    )


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "ok"}
