from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class DiscountRequest(BaseModel):
    """
    Schema for discount application request
    """
    amount: Decimal = Field(..., description="Amount to apply discount to", ge=0)
    coupon_code: Optional[str] = Field(None, description="Coupon code to apply, if any")


class DiscountRule(BaseModel):
    """
    Schema for discount rule
    """
    name: str
    description: str
    discount_percent: Decimal
    discount_type: str


class DiscountResponse(BaseModel):
    """
    Schema for discount application response
    """
    original_amount: Decimal
    discount_amount: Decimal
    final_amount: Decimal
    discount_rule: Optional[DiscountRule] = None
    coupon_code: Optional[str] = None


class DiscountAppliedEvent(BaseModel):
    """
    Schema for discount applied event
    """
    event_id: str
    event_type: str = "discount_applied"
    timestamp: str
    correlation_id: str
    payload: dict
