from decimal import Decimal
from typing import Dict, Any

from sqlalchemy.orm import Session

from app.core.event_publisher import event_publisher
from app.repositories.discount_repository import discount_repository
from app.schemas.discount import DiscountResponse, DiscountRule


class DiscountService:
    """
    Service layer for discount operations - contains business logic
    """
    
    async def apply_discount(
        self, 
        db: Session, 
        amount: Decimal, 
        coupon_code: str = None, 
        user_id: str = None,
        correlation_id: str = None
    ) -> DiscountResponse:
        """
        Apply discount to an amount based on coupon, user type, or amount threshold
        
        This is the main business logic for discount applications.
        Priority: 1. Coupon code, 2. User type, 3. Amount-based.
        It publishes an event after applying the discount.
        """
        discount_amount = Decimal('0.0')
        discount_rule = None
        coupon_id = None
        discount_type = "none"
        
        # Try to apply coupon code discount if provided
        if coupon_code:
            coupon = discount_repository.get_coupon_by_code(db, coupon_code)
            
            if coupon:
                discount_percent = Decimal(str(coupon.discount_percent))
                discount_amount = amount * (discount_percent / 100)
                
                # Apply max discount cap if set
                if coupon.max_discount_amount:
                    max_discount = Decimal(str(coupon.max_discount_amount))
                    if discount_amount > max_discount:
                        discount_amount = max_discount
                
                discount_rule = DiscountRule(
                    name=f"Coupon: {coupon_code}",
                    description=coupon.description or "Coupon discount",
                    discount_percent=discount_percent,
                    discount_type="coupon"
                )
                
                coupon_id = coupon.id
                discount_type = "coupon"
        
        # If no coupon discount, try user type discount (simplified, would need user service integration)
        # This is just a placeholder for the real implementation
        if discount_amount == Decimal('0.0') and user_id:
            # In a real system, you would get user type from user service or JWT claims
            # Here we'll just simulate a basic user type check
            user_type = "regular"  # This would come from a user service or auth token
            
            user_discount = discount_repository.get_user_type_discount(db, user_type)
            
            if user_discount:
                discount_percent = Decimal(str(user_discount.discount_percent))
                discount_amount = amount * (discount_percent / 100)
                
                discount_rule = DiscountRule(
                    name=f"User Type: {user_type}",
                    description=f"Discount for {user_type} users",
                    discount_percent=discount_percent,
                    discount_type="user_type"
                )
                
                discount_type = "user_type"
        
        # If still no discount, try amount-based discount
        if discount_amount == Decimal('0.0'):
            amount_discount = discount_repository.get_amount_based_discount(db, amount)
            
            if amount_discount:
                discount_percent = Decimal(str(amount_discount.discount_percent))
                discount_amount = amount * (discount_percent / 100)
                
                discount_rule = DiscountRule(
                    name=f"Amount Based",
                    description=f"Discount for orders over {amount_discount.min_amount}",
                    discount_percent=discount_percent,
                    discount_type="amount_based"
                )
                
                discount_type = "amount_based"
        
        # Calculate final amount
        final_amount = amount - discount_amount
        
        # Record the discount application if any discount was applied
        if discount_amount > Decimal('0.0'):
            discount_repository.create_discount_application(
                db=db,
                user_id=user_id,
                original_amount=amount,
                discount_amount=discount_amount,
                final_amount=final_amount,
                discount_type=discount_type,
                coupon_id=coupon_id,
                correlation_id=correlation_id
            )
            
            # Publish discount applied event
            await event_publisher.publish_discount_applied(
                discount_data={
                    "discount_amount": float(discount_amount),
                    "original_amount": float(amount),
                    "final_amount": float(final_amount),
                    "discount_type": discount_type,
                    "coupon_code": coupon_code,
                    "user_id": user_id
                },
                correlation_id=correlation_id
            )
        
        # Create response object
        response = DiscountResponse(
            original_amount=amount,
            discount_amount=discount_amount,
            final_amount=final_amount,
            discount_rule=discount_rule,
            coupon_code=coupon_code if discount_type == "coupon" else None
        )
        
        return response


# Singleton instance
discount_service = DiscountService()
