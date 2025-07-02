import pytest
from unittest.mock import MagicMock, patch
from app.services.invoice_service import InvoiceService
from app.models.invoice_model import Invoice, InvoiceItem

@pytest.fixture
def invoice_service():
    return InvoiceService()

def test_create_invoice():
    """Test invoice creation"""
    # Arrange
    invoice_service = InvoiceService()
    
    # Mock the database session
    mock_session = MagicMock()
    mock_session.add = MagicMock()
    mock_session.commit = MagicMock()
    
    # Mock the external service calls
    invoice_service.get_tax_amount = MagicMock(return_value=9.25)
    invoice_service.get_discount_amount = MagicMock(return_value=10.0)
    
    with patch("app.services.invoice_service.get_db", return_value=mock_session):
        # Act
        invoice_data = {
            "customer_id": "cust123",
            "items": [
                {"product_id": "prod1", "quantity": 2, "unit_price": 50.0},
                {"product_id": "prod2", "quantity": 1, "unit_price": 30.0}
            ],
            "discount_code": "SUMMER10",
            "billing_address": {
                "country": "US",
                "state": "CA",
                "city": "San Francisco",
                "street": "123 Main St",
                "postal_code": "94105"
            }
        }
        
        result = invoice_service.create_invoice(invoice_data)
        
        # Assert
        assert mock_session.add.called
        assert mock_session.commit.called
        invoice_service.get_tax_amount.assert_called_once()
        invoice_service.get_discount_amount.assert_called_once()
        assert result.subtotal == 130.0  # 2*50 + 1*30
        assert result.tax_amount == 9.25
        assert result.discount_amount == 10.0
        assert result.total_amount == 129.25  # 130 + 9.25 - 10

@pytest.mark.asyncio
async def test_process_invoice_creation_event():
    """Test processing invoice creation event"""
    # Arrange
    invoice_service = InvoiceService()
    event_data = {
        "order_id": "order123",
        "customer_id": "cust123",
        "items": [
            {"product_id": "prod1", "quantity": 2, "unit_price": 50.0}
        ],
        "discount_code": "SUMMER10",
        "billing_address": {
            "country": "US",
            "state": "CA",
            "city": "San Francisco",
            "street": "123 Main St",
            "postal_code": "94105"
        }
    }
    
    # Mock methods
    invoice_service.create_invoice = MagicMock(return_value=MagicMock(id="inv123"))
    invoice_service.generate_pdf = MagicMock()
    invoice_service.publish_invoice_created_event = MagicMock()
    
    # Act
    await invoice_service.process_invoice_creation_event(event_data)
    
    # Assert
    invoice_service.create_invoice.assert_called_once()
    invoice_service.generate_pdf.assert_called_once()
    invoice_service.publish_invoice_created_event.assert_called_once()

def test_get_invoice_by_id():
    """Test getting invoice by ID"""
    # Arrange
    invoice_service = InvoiceService()
    mock_invoice = Invoice(
        id="inv123",
        customer_id="cust123",
        subtotal=100.0,
        tax_amount=9.25,
        discount_amount=10.0,
        total_amount=99.25,
        status="issued"
    )
    
    # Mock the database session
    mock_session = MagicMock()
    mock_session.query().filter().first.return_value = mock_invoice
    
    with patch("app.services.invoice_service.get_db", return_value=mock_session):
        # Act
        result = invoice_service.get_invoice_by_id("inv123")
        
        # Assert
        assert result.id == "inv123"
        assert result.customer_id == "cust123"
        assert result.total_amount == 99.25

def test_get_invoice_not_found():
    """Test getting invoice when not found"""
    # Arrange
    invoice_service = InvoiceService()
    
    # Mock the database session
    mock_session = MagicMock()
    mock_session.query().filter().first.return_value = None
    
    with patch("app.services.invoice_service.get_db", return_value=mock_session):
        # Act & Assert
        with pytest.raises(ValueError, match="Invoice not found: invalid-id"):
            invoice_service.get_invoice_by_id("invalid-id")
