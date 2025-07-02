from decimal import Decimal
from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.discount import (
    DiscountCoupon, 
    UserTypeDiscount, 
    AmountBasedDiscount,
    DiscountApplication
)


class DiscountRepository:
    """
    Repository for discount operations, follows the repository pattern
    to abstract database operations
    """
    
    def get_coupon_by_code(self, db: Session, code: str) -> Optional[DiscountCoupon]:
        """Get a discount coupon by its code"""
        return db.query(DiscountCoupon).filter(
            DiscountCoupon.code == code,
            DiscountCoupon.is_active == True,
            (DiscountCoupon.valid_until == None) | (DiscountCoupon.valid_until > datetime.utcnow())
        ).first()
    
    def get_user_type_discount(self, db: Session, user_type: str) -> Optional[UserTypeDiscount]:
        """Get discount for a specific user type"""
        return db.query(UserTypeDiscount).filter(
            UserTypeDiscount.user_type == user_type
        ).first()
    
    def get_amount_based_discount(self, db: Session, amount: Decimal) -> Optional[AmountBasedDiscount]:
        """Get discount based on amount"""
        return db.query(AmountBasedDiscount).filter(
            AmountBasedDiscount.min_amount <= amount,
            (AmountBasedDiscount.max_amount == None) | (AmountBasedDiscount.max_amount >= amount)
        ).order_by(AmountBasedDiscount.discount_percent.desc()).first()
    
    def create_discount_application(
        self,
        db: Session,
        user_id: str,
        original_amount: Decimal,
        discount_amount: Decimal,
        final_amount: Decimal,
        discount_type: str,
        coupon_id: Optional[int] = None,
        correlation_id: str = None
    ) -> DiscountApplication:
        """Record a discount application"""
        db_application = DiscountApplication(
            user_id=user_id,
            original_amount=float(original_amount),
            discount_amount=float(discount_amount),
            final_amount=float(final_amount),
            discount_type=discount_type,
            coupon_id=coupon_id,
            correlation_id=correlation_id
        )
        db.add(db_application)
        db.commit()
        db.refresh(db_application)
        return db_application
    
    def get_discount_history_by_user(
        self,
        db: Session,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[DiscountApplication]:
        """Get discount application history for a user"""
        return db.query(DiscountApplication).filter(
            DiscountApplication.user_id == user_id
        ).order_by(DiscountApplication.created_at.desc()).offset(skip).limit(limit).all()


# Singleton instance
discount_repository = DiscountRepository()
