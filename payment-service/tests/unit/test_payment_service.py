import pytest
from unittest.mock import MagicMock, patch
from app.services.payment_service import PaymentService
from app.models.payment_model import Payment

@pytest.fixture
def payment_service():
    return PaymentService()

def test_process_payment():
    """Test payment processing"""
    # Arrange
    payment_service = PaymentService()
    payment_data = {
        "invoice_id": "inv123",
        "amount": 99.25,
        "payment_method": {
            "type": "credit_card",
            "card_number": "4111111111111111",
            "expiry_month": 12,
            "expiry_year": 2025,
            "cvv": "123"
        },
        "customer_id": "cust123"
    }
    
    # Mock payment gateway response
    mock_gateway_response = {
        "transaction_id": "txn123",
        "status": "success",
        "message": "Payment processed successfully"
    }
    
    # Mock the payment gateway call
    payment_service.call_payment_gateway = MagicMock(return_value=mock_gateway_response)
    
    # Mock the database session
    mock_session = MagicMock()
    mock_session.add = MagicMock()
    mock_session.commit = MagicMock()
    
    with patch("app.services.payment_service.get_db", return_value=mock_session):
        # Act
        result = payment_service.process_payment(payment_data)
        
        # Assert
        assert result.transaction_id == "txn123"
        assert result.status == "success"
        payment_service.call_payment_gateway.assert_called_once()
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_process_payment_event():
    """Test processing payment event"""
    # Arrange
    payment_service = PaymentService()
    event_data = {
        "invoice_id": "inv123",
        "amount": 99.25,
        "payment_method": {
            "type": "credit_card",
            "card_number": "4111111111111111",
            "expiry_month": 12,
            "expiry_year": 2025,
            "cvv": "123"
        },
        "customer_id": "cust123"
    }
    
    # Mock methods
    payment_result = MagicMock(
        transaction_id="txn123",
        status="success",
        invoice_id="inv123"
    )
    payment_service.process_payment = MagicMock(return_value=payment_result)
    payment_service.publish_payment_processed_event = MagicMock()
    payment_service.update_invoice_status = MagicMock()
    
    # Act
    await payment_service.process_payment_event(event_data)
    
    # Assert
    payment_service.process_payment.assert_called_once_with(event_data)
    payment_service.publish_payment_processed_event.assert_called_once()
    payment_service.update_invoice_status.assert_called_once_with("inv123", "paid")

def test_get_payment_by_invoice_id():
    """Test getting payment by invoice ID"""
    # Arrange
    payment_service = PaymentService()
    mock_payment = Payment(
        id="pay123",
        invoice_id="inv123",
        amount=99.25,
        transaction_id="txn123",
        status="success",
        payment_method="credit_card",
        customer_id="cust123"
    )
    
    # Mock the database session
    mock_session = MagicMock()
    mock_session.query().filter().first.return_value = mock_payment
    
    with patch("app.services.payment_service.get_db", return_value=mock_session):
        # Act
        result = payment_service.get_payment_by_invoice_id("inv123")
        
        # Assert
        assert result.id == "pay123"
        assert result.invoice_id == "inv123"
        assert result.transaction_id == "txn123"
        assert result.status == "success"

def test_get_payment_not_found():
    """Test getting payment when not found"""
    # Arrange
    payment_service = PaymentService()
    
    # Mock the database session
    mock_session = MagicMock()
    mock_session.query().filter().first.return_value = None
    
    with patch("app.services.payment_service.get_db", return_value=mock_session):
        # Act & Assert
        with pytest.raises(ValueError, match="Payment not found for invoice: invalid-id"):
            payment_service.get_payment_by_invoice_id("invalid-id")

def test_call_payment_gateway_failure():
    """Test payment gateway failure handling"""
    # Arrange
    payment_service = PaymentService()
    payment_data = {
        "invoice_id": "inv123",
        "amount": 99.25,
        "payment_method": {
            "type": "credit_card",
            "card_number": "4111111111111111",
            "expiry_month": 12,
            "expiry_year": 2025,
            "cvv": "123"
        },
        "customer_id": "cust123"
    }
    
    # Mock the HTTP client
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "status": "failed",
        "message": "Insufficient funds",
        "transaction_id": "txn456"
    }
    mock_response.status_code = 400
    
    with patch("httpx.AsyncClient.post", return_value=mock_response):
        # Act & Assert
        with pytest.raises(ValueError, match="Payment failed: Insufficient funds"):
            payment_service.call_payment_gateway(payment_data)
