import uuid
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from loguru import logger

from app.models.invoice import InvoiceStatus
from app.repositories.invoice_repository import invoice_repository
from app.core.event_publisher import event_publisher
from app.core.config import settings


class InvoiceService:
    """
    Service layer for invoice operations - contains business logic
    """
    
    async def create_invoice(
        self,
        db: Session,
        user_id: str,
        customer_id: str,
        customer_name: str,
        customer_email: str,
        customer_address: Optional[str],
        subtotal: Decimal,
        tax_amount: Decimal,
        discount_amount: Decimal,
        items: List[Dict],
        notes: Optional[str] = None,
        due_date: Optional[datetime] = None,
        status: InvoiceStatus = InvoiceStatus.DRAFT,
        correlation_id: Optional[str] = None
    ):
        """
        Create a new invoice
        
        This method creates a new invoice record, adds the invoice items,
        calculates the total amount, and publishes an invoice_created event.
        """
        # Generate invoice number
        invoice_number = self._generate_invoice_number()
        
        # Calculate total amount
        total_amount = subtotal + tax_amount - discount_amount
        
        # Create invoice
        db_invoice = invoice_repository.create_invoice(
            db=db,
            user_id=user_id,
            invoice_number=invoice_number,
            customer_id=customer_id,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_address=customer_address,
            subtotal=float(subtotal),
            tax_amount=float(tax_amount),
            discount_amount=float(discount_amount),
            total_amount=float(total_amount),
            notes=notes,
            due_date=due_date,
            status=status,
            correlation_id=correlation_id
        )
        
        # Create invoice items
        for item in items:
            quantity = Decimal(str(item["quantity"]))
            unit_price = Decimal(str(item["unit_price"]))
            amount = quantity * unit_price
            
            invoice_repository.add_invoice_item(
                db=db,
                invoice_id=db_invoice.id,
                description=item["description"],
                quantity=float(quantity),
                unit_price=float(unit_price),
                amount=float(amount)
            )
        
        # Publish invoice created event
        if status != InvoiceStatus.DRAFT:
            await event_publisher.publish_invoice_created(
                invoice_data={
                    "id": db_invoice.id,
                    "invoice_number": db_invoice.invoice_number,
                    "customer_id": db_invoice.customer_id,
                    "amount": float(total_amount),
                    "tax_amount": float(tax_amount),
                    "discount_amount": float(discount_amount),
                    "total_amount": float(total_amount),
                    "status": db_invoice.status,
                    "created_at": db_invoice.created_at.isoformat(),
                    "due_date": db_invoice.due_date.isoformat() if db_invoice.due_date else None,
                    "user_id": user_id
                },
                correlation_id=correlation_id
            )
        
        return db_invoice
    
    def get_invoice(self, db: Session, invoice_id: int, user_id: str):
        """Get an invoice by ID"""
        invoice = invoice_repository.get_invoice_by_id(db, invoice_id)
        
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice with ID {invoice_id} not found"
            )
            
        # Check if user has access to this invoice
        if invoice.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this invoice"
            )
            
        return invoice
    
    def get_user_invoices(
        self,
        db: Session,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ):
        """Get all invoices for a user"""
        return invoice_repository.get_invoices_by_user(db, user_id, skip, limit)
    
    def get_customer_invoices(
        self,
        db: Session,
        user_id: str,
        customer_id: str,
        skip: int = 0,
        limit: int = 100
    ):
        """Get all invoices for a customer"""
        # Get the invoices
        invoices = invoice_repository.get_invoices_by_customer(db, customer_id, skip, limit)
        
        # Filter by user_id for security
        return [inv for inv in invoices if inv.user_id == user_id]
    
    async def update_invoice(
        self,
        db: Session,
        invoice_id: int,
        user_id: str,
        update_data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ):
        """Update an invoice"""
        invoice = self.get_invoice(db, invoice_id, user_id)
        
        # Can only update draft invoices
        if invoice.status != InvoiceStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only update draft invoices"
            )
        
        updated_invoice = invoice_repository.update_invoice(
            db=db,
            invoice=invoice,
            user_id=user_id,
            update_data=update_data,
            correlation_id=correlation_id
        )
        
        return updated_invoice
    
    async def issue_invoice(
        self,
        db: Session,
        invoice_id: int,
        user_id: str,
        correlation_id: Optional[str] = None
    ):
        """Issue an invoice (change status from DRAFT to ISSUED)"""
        invoice = self.get_invoice(db, invoice_id, user_id)
        
        # Can only issue draft invoices
        if invoice.status != InvoiceStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Can only issue draft invoices. Current status: {invoice.status}"
            )
        
        # Update invoice status
        updated_invoice = invoice_repository.update_invoice_status(
            db=db,
            invoice=invoice,
            user_id=user_id,
            status=InvoiceStatus.ISSUED,
            correlation_id=correlation_id
        )
        
        # Publish invoice created event
        await event_publisher.publish_invoice_created(
            invoice_data={
                "id": updated_invoice.id,
                "invoice_number": updated_invoice.invoice_number,
                "customer_id": updated_invoice.customer_id,
                "amount": updated_invoice.total_amount,
                "tax_amount": updated_invoice.tax_amount,
                "discount_amount": updated_invoice.discount_amount,
                "total_amount": updated_invoice.total_amount,
                "status": updated_invoice.status,
                "created_at": updated_invoice.created_at.isoformat(),
                "due_date": updated_invoice.due_date.isoformat() if updated_invoice.due_date else None,
                "user_id": user_id
            },
            correlation_id=correlation_id
        )
        
        # Generate PDF if enabled
        if settings.PDF_GENERATION_ENABLED:
            await self._generate_invoice_pdf(updated_invoice)
        
        return updated_invoice
    
    async def cancel_invoice(
        self,
        db: Session,
        invoice_id: int,
        user_id: str,
        correlation_id: Optional[str] = None
    ):
        """Cancel an invoice"""
        invoice = self.get_invoice(db, invoice_id, user_id)
        
        # Cannot cancel paid invoices
        if invoice.status == InvoiceStatus.PAID:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel paid invoices"
            )
        
        # Update invoice status
        updated_invoice = invoice_repository.update_invoice_status(
            db=db,
            invoice=invoice,
            user_id=user_id,
            status=InvoiceStatus.CANCELLED,
            correlation_id=correlation_id
        )
        
        # Publish invoice updated event
        await event_publisher.publish_invoice_updated(
            invoice_data={
                "id": updated_invoice.id,
                "invoice_number": updated_invoice.invoice_number,
                "customer_id": updated_invoice.customer_id,
                "status": updated_invoice.status,
                "user_id": user_id
            },
            correlation_id=correlation_id
        )
        
        return updated_invoice
    
    def get_invoice_payments(self, db: Session, invoice_id: int, user_id: str):
        """Get all payments for an invoice"""
        # Verify access to invoice
        invoice = self.get_invoice(db, invoice_id, user_id)
        
        # Get payments
        return invoice_repository.get_invoice_payments(db, invoice_id)
    
    def get_invoice_history(self, db: Session, invoice_id: int, user_id: str):
        """Get the history for an invoice"""
        # Verify access to invoice
        invoice = self.get_invoice(db, invoice_id, user_id)
        
        # Get history
        return invoice_repository.get_invoice_history(db, invoice_id)
    
    def _generate_invoice_number(self) -> str:
        """Generate a unique invoice number"""
        timestamp = int(datetime.utcnow().timestamp())
        random_part = str(uuid.uuid4().int)[:8]
        return f"INV-{timestamp}-{random_part}"
    
    async def _generate_invoice_pdf(self, invoice):
        """
        Generate a PDF for an invoice
        
        This is a placeholder for actual PDF generation functionality.
        In a real implementation, this would use a library like reportlab or
        an HTML-to-PDF converter to generate a proper invoice PDF.
        """
        # Create PDF directory if it doesn't exist
        os.makedirs(settings.PDF_STORAGE_PATH, exist_ok=True)
        
        pdf_path = os.path.join(settings.PDF_STORAGE_PATH, f"{invoice.invoice_number}.pdf")
        
        # Placeholder for actual PDF generation
        logger.info(f"PDF would be generated at: {pdf_path}")
        
        # In a real implementation, this would return the path to the generated PDF
        return pdf_path


async def handle_payment_received(event):
    """
    Handle payment_received event
    
    This function is called when a payment_received event is consumed.
    It updates the invoice status and records the payment.
    """
    # This would be implemented with a database session context
    # and actual business logic to record the payment and update invoice status
    logger.info(f"Handling payment_received event: {event.get('event_id')}")
    
    # In a real implementation, this would:
    # 1. Extract payment data from event
    # 2. Get the invoice by invoice number or ID
    # 3. Record the payment
    # 4. Update invoice status (PAID or PARTIALLY_PAID)
    # 5. Publish invoice updated event


# Singleton instance
invoice_service = InvoiceService()
