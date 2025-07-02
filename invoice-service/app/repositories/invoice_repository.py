from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.invoice import Invoice, InvoiceItem, InvoicePayment, InvoiceHistory, InvoiceStatus


class InvoiceRepository:
    """
    Repository for invoice operations, follows the repository pattern
    to abstract database operations
    """
    
    def create_invoice(
        self,
        db: Session,
        user_id: str,
        invoice_number: str,
        customer_id: str,
        customer_name: str,
        customer_email: str,
        customer_address: Optional[str],
        subtotal: float,
        tax_amount: float,
        discount_amount: float,
        total_amount: float,
        notes: Optional[str] = None,
        due_date: Optional[datetime] = None,
        status: InvoiceStatus = InvoiceStatus.DRAFT,
        correlation_id: Optional[str] = None
    ) -> Invoice:
        """Create a new invoice"""
        db_invoice = Invoice(
            user_id=user_id,
            invoice_number=invoice_number,
            customer_id=customer_id,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_address=customer_address,
            subtotal=subtotal,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            notes=notes,
            due_date=due_date,
            status=status
        )
        db.add(db_invoice)
        db.commit()
        db.refresh(db_invoice)
        
        # Add history entry
        self.add_history_entry(
            db,
            invoice_id=db_invoice.id,
            user_id=user_id,
            action="created",
            details=f"Invoice {invoice_number} created"
        )
        
        return db_invoice
    
    def add_invoice_item(
        self,
        db: Session,
        invoice_id: int,
        description: str,
        quantity: float,
        unit_price: float,
        amount: float
    ) -> InvoiceItem:
        """Add an item to an invoice"""
        db_item = InvoiceItem(
            invoice_id=invoice_id,
            description=description,
            quantity=quantity,
            unit_price=unit_price,
            amount=amount
        )
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item
    
    def get_invoice_by_id(self, db: Session, invoice_id: int) -> Optional[Invoice]:
        """Get an invoice by ID"""
        return db.query(Invoice).filter(Invoice.id == invoice_id).first()
    
    def get_invoice_by_number(self, db: Session, invoice_number: str) -> Optional[Invoice]:
        """Get an invoice by invoice number"""
        return db.query(Invoice).filter(Invoice.invoice_number == invoice_number).first()
    
    def get_invoices_by_user(
        self,
        db: Session,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Invoice]:
        """Get all invoices for a user"""
        return db.query(Invoice).filter(
            Invoice.user_id == user_id
        ).order_by(desc(Invoice.created_at)).offset(skip).limit(limit).all()
    
    def get_invoices_by_customer(
        self,
        db: Session,
        customer_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Invoice]:
        """Get all invoices for a customer"""
        return db.query(Invoice).filter(
            Invoice.customer_id == customer_id
        ).order_by(desc(Invoice.created_at)).offset(skip).limit(limit).all()
    
    def update_invoice(
        self,
        db: Session,
        invoice: Invoice,
        user_id: str,
        update_data: dict,
        correlation_id: Optional[str] = None
    ) -> Invoice:
        """Update an invoice"""
        details = []
        
        for key, value in update_data.items():
            if hasattr(invoice, key) and getattr(invoice, key) != value:
                details.append(f"{key}: {getattr(invoice, key)} -> {value}")
                setattr(invoice, key, value)
        
        if details:
            invoice.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(invoice)
            
            # Add history entry
            self.add_history_entry(
                db,
                invoice_id=invoice.id,
                user_id=user_id,
                action="updated",
                details=", ".join(details)
            )
        
        return invoice
    
    def update_invoice_status(
        self,
        db: Session,
        invoice: Invoice,
        user_id: str,
        status: InvoiceStatus,
        correlation_id: Optional[str] = None
    ) -> Invoice:
        """Update an invoice status"""
        if invoice.status != status:
            old_status = invoice.status
            invoice.status = status
            
            # If changing to paid status, record paid date
            if status == InvoiceStatus.PAID and invoice.paid_date is None:
                invoice.paid_date = datetime.utcnow()
            
            invoice.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(invoice)
            
            # Add history entry
            self.add_history_entry(
                db,
                invoice_id=invoice.id,
                user_id=user_id,
                action="status_change",
                details=f"Status changed from {old_status} to {status}"
            )
        
        return invoice
    
    def add_payment(
        self,
        db: Session,
        invoice_id: int,
        payment_id: str,
        amount: float,
        payment_method: str,
        transaction_reference: Optional[str] = None
    ) -> InvoicePayment:
        """Add a payment to an invoice"""
        db_payment = InvoicePayment(
            invoice_id=invoice_id,
            payment_id=payment_id,
            amount=amount,
            payment_method=payment_method,
            transaction_reference=transaction_reference
        )
        db.add(db_payment)
        db.commit()
        db.refresh(db_payment)
        return db_payment
    
    def get_invoice_payments(self, db: Session, invoice_id: int) -> List[InvoicePayment]:
        """Get all payments for an invoice"""
        return db.query(InvoicePayment).filter(
            InvoicePayment.invoice_id == invoice_id
        ).order_by(InvoicePayment.payment_date).all()
    
    def add_history_entry(
        self,
        db: Session,
        invoice_id: int,
        user_id: str,
        action: str,
        details: str
    ) -> InvoiceHistory:
        """Add a history entry for an invoice"""
        db_history = InvoiceHistory(
            invoice_id=invoice_id,
            user_id=user_id,
            action=action,
            details=details
        )
        db.add(db_history)
        db.commit()
        db.refresh(db_history)
        return db_history
    
    def get_invoice_history(
        self,
        db: Session,
        invoice_id: int
    ) -> List[InvoiceHistory]:
        """Get the history for an invoice"""
        return db.query(InvoiceHistory).filter(
            InvoiceHistory.invoice_id == invoice_id
        ).order_by(desc(InvoiceHistory.created_at)).all()


# Singleton instance
invoice_repository = InvoiceRepository()
