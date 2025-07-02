from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.tax import TaxRule as TaxRuleModel
from app.models.tax import TaxCalculation as TaxCalculationModel


class TaxRepository:
    """
    Repository for tax calculations and rules, follows the repository pattern
    to abstract database operations
    """
    
    def get_tax_rules_by_product_type(self, db: Session, product_type: str) -> List[TaxRuleModel]:
        """Get tax rules for a specific product type"""
        return db.query(TaxRuleModel).filter(TaxRuleModel.product_type == product_type).all()
    
    def get_default_tax_rule(self, db: Session) -> Optional[TaxRuleModel]:
        """Get default tax rule when no specific rules apply"""
        return db.query(TaxRuleModel).filter(
            TaxRuleModel.name == "default"
        ).first()
    
    def create_tax_calculation(
        self, 
        db: Session, 
        user_id: str, 
        original_amount: Decimal,
        tax_amount: Decimal,
        total_amount: Decimal,
        product_type: str,
        rule_id: int,
        correlation_id: str
    ) -> TaxCalculationModel:
        """Create a record of a tax calculation"""
        db_calculation = TaxCalculationModel(
            user_id=user_id,
            original_amount=float(original_amount),
            tax_amount=float(tax_amount),
            total_amount=float(total_amount),
            product_type=product_type,
            rule_id=rule_id,
            correlation_id=correlation_id
        )
        db.add(db_calculation)
        db.commit()
        db.refresh(db_calculation)
        return db_calculation
    
    def get_calculation_history_by_user(
        self, 
        db: Session, 
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[TaxCalculationModel]:
        """Get tax calculation history for a user"""
        return db.query(TaxCalculationModel).filter(
            TaxCalculationModel.user_id == user_id
        ).order_by(TaxCalculationModel.created_at.desc()).offset(skip).limit(limit).all()


# Singleton instance
tax_repository = TaxRepository()
