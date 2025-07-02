from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class TaxRule(Base):
    """
    Tax rule model for storing different tax rates and rules
    """
    __tablename__ = "tax_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    rate = Column(Float, nullable=False)
    product_type = Column(String, index=True, nullable=False)
    country_code = Column(String(2), index=True, nullable=False)
    region_code = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with tax calculations
    calculations = relationship("TaxCalculation", back_populates="rule")


class TaxCalculation(Base):
    """
    Tax calculation model for storing calculation history
    """
    __tablename__ = "tax_calculations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    original_amount = Column(Float, nullable=False)
    tax_amount = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    product_type = Column(String, nullable=False)
    rule_id = Column(Integer, ForeignKey("tax_rules.id"), nullable=False)
    correlation_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship with tax rule
    rule = relationship("TaxRule", back_populates="calculations")
