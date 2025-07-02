import pytest
from unittest.mock import MagicMock, patch
from app.services.discount_service import DiscountService
from app.models.discount_model import Discount

@pytest.fixture
def discount_service():
    return DiscountService()

def test_calculate_discount():
    """Test discount calculation with different types"""
    # Arrange
    discount_service = DiscountService()
    discount = Discount(code="SUMMER10", type="percentage", value=10.0)
    
    # Mock the database call
    discount_service.get_discount = MagicMock(return_value=discount)
    
    # Act
    result = discount_service.calculate_discount(amount=100.0, code="SUMMER10")
    
    # Assert
    assert result == 10.0
    discount_service.get_discount.assert_called_once_with(code="SUMMER10")

def test_calculate_fixed_discount():
    """Test fixed discount calculation"""
    # Arrange
    discount_service = DiscountService()
    discount = Discount(code="FLAT20", type="fixed", value=20.0)
    
    # Mock the database call
    discount_service.get_discount = MagicMock(return_value=discount)
    
    # Act
    result = discount_service.calculate_discount(amount=100.0, code="FLAT20")
    
    # Assert
    assert result == 20.0

@pytest.mark.asyncio
async def test_process_discount_calculation_event():
    """Test processing discount calculation event"""
    # Arrange
    discount_service = DiscountService()
    event_data = {
        "order_id": "12345",
        "amount": 100.0,
        "discount_code": "SUMMER10"
    }
    
    # Mock the calculate_discount method
    discount_service.calculate_discount = MagicMock(return_value=10.0)
    discount_service.publish_discount_calculated_event = MagicMock()
    
    # Act
    await discount_service.process_discount_calculation_event(event_data)
    
    # Assert
    discount_service.calculate_discount.assert_called_once_with(
        amount=100.0, code="SUMMER10"
    )
    discount_service.publish_discount_calculated_event.assert_called_once_with(
        order_id="12345", amount=100.0, discount_amount=10.0
    )

def test_get_discount_not_found():
    """Test getting discount when not found"""
    # Arrange
    discount_service = DiscountService()
    
    # Mock the database session
    mock_session = MagicMock()
    mock_session.query().filter().first.return_value = None
    
    with patch("app.services.discount_service.get_db", return_value=mock_session):
        # Act & Assert
        with pytest.raises(ValueError, match="Discount code not found: INVALID"):
            discount_service.get_discount(code="INVALID")
