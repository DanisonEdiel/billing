from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class DiscountCoupon(Base):
    """
    Discount coupon model
    """
    __tablename__ = "discount_coupons"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, index=True, unique=True, nullable=False)
    description = Column(String, nullable=True)
    discount_percent = Column(Float, nullable=False)
    max_discount_amount = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    valid_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with discount applications
    applications = relationship("DiscountApplication", back_populates="coupon")


class UserTypeDiscount(Base):
    """
    User type discount model
    """
    __tablename__ = "user_type_discounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_type = Column(String, index=True, nullable=False)
    discount_percent = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AmountBasedDiscount(Base):
    """
    Amount based discount model
    """
    __tablename__ = "amount_based_discounts"
    
    id = Column(Integer, primary_key=True, index=True)
    min_amount = Column(Float, nullable=False)
    max_amount = Column(Float, nullable=True)
    discount_percent = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DiscountApplication(Base):
    """
    Discount application model
    """
    __tablename__ = "discount_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    original_amount = Column(Float, nullable=False)
    discount_amount = Column(Float, nullable=False)
    final_amount = Column(Float, nullable=False)
    discount_type = Column(String, nullable=False)  # 'coupon', 'user_type', 'amount_based'
    coupon_id = Column(Integer, ForeignKey("discount_coupons.id"), nullable=True)
    correlation_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship with discount coupon
    coupon = relationship("DiscountCoupon", back_populates="applications")
