import pytest
from unittest.mock import MagicMock, patch
from app.services.tax_service import TaxService
from app.models.tax_model import TaxRate

@pytest.fixture
def tax_service():
    return TaxService()

def test_calculate_tax():
    """Test tax calculation with different rates"""
    # Arrange
    tax_service = TaxService()
    tax_rate = TaxRate(country="US", state="CA", rate=0.0925)
    
    # Mock the database call
    tax_service.get_tax_rate = MagicMock(return_value=tax_rate)
    
    # Act
    result = tax_service.calculate_tax(amount=100.0, country="US", state="CA")
    
    # Assert
    assert result == 9.25
    tax_service.get_tax_rate.assert_called_once_with(country="US", state="CA")

@pytest.mark.asyncio
async def test_process_tax_calculation_event():
    """Test processing tax calculation event"""
    # Arrange
    tax_service = TaxService()
    event_data = {
        "order_id": "12345",
        "amount": 100.0,
        "country": "US",
        "state": "CA"
    }
    
    # Mock the calculate_tax method
    tax_service.calculate_tax = MagicMock(return_value=9.25)
    tax_service.publish_tax_calculated_event = MagicMock()
    
    # Act
    await tax_service.process_tax_calculation_event(event_data)
    
    # Assert
    tax_service.calculate_tax.assert_called_once_with(
        amount=100.0, country="US", state="CA"
    )
    tax_service.publish_tax_calculated_event.assert_called_once_with(
        order_id="12345", amount=100.0, tax_amount=9.25
    )

def test_get_tax_rate_not_found():
    """Test getting tax rate when not found"""
    # Arrange
    tax_service = TaxService()
    
    # Mock the database session
    mock_session = MagicMock()
    mock_session.query().filter().first.return_value = None
    
    with patch("app.services.tax_service.get_db", return_value=mock_session):
        # Act & Assert
        with pytest.raises(ValueError, match="Tax rate not found for country: US, state: NY"):
            tax_service.get_tax_rate(country="US", state="NY")
