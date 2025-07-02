from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class TaxCalculationRequest(BaseModel):
    """
    Schema for tax calculation request
    """
    amount: Decimal = Field(..., description="Amount to calculate tax for", ge=0)
    product_type: str = Field(..., description="Type of product (e.g., 'physical', 'digital', 'service')")
    
    @validator("product_type")
    def validate_product_type(cls, v):
        valid_types = ["physical", "digital", "service"]
        if v.lower() not in valid_types:
            raise ValueError(f"Product type must be one of: {', '.join(valid_types)}")
        return v.lower()


class TaxRule(BaseModel):
    """
    Schema for tax rule
    """
    name: str
    description: str
    rate: Decimal


class TaxCalculationResponse(BaseModel):
    """
    Schema for tax calculation response
    """
    original_amount: Decimal
    tax_amount: Decimal
    rules_applied: List[TaxRule]
    total_amount: Decimal


class TaxCalculatedEvent(BaseModel):
    """
    Schema for tax calculated event
    """
    event_id: str
    event_type: str = "tax_calculated"
    timestamp: str
    correlation_id: str
    payload: dict
