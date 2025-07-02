from decimal import Decimal
from typing import List, Dict, Any

from sqlalchemy.orm import Session

from app.core.event_publisher import event_publisher
from app.repositories.tax_repository import tax_repository
from app.schemas.tax import TaxCalculationResponse, TaxRule


class TaxService:
    """
    Service layer for tax calculations - contains business logic
    """
    
    async def calculate_tax(
        self, 
        db: Session, 
        amount: Decimal, 
        product_type: str, 
        user_id: str,
        correlation_id: str
    ) -> TaxCalculationResponse:
        """
        Calculate tax for a given amount and product type
        
        This is the main business logic for tax calculations.
        It applies tax rules based on product type and publishes
        an event after calculation.
        """
        # Get applicable tax rules
        db_tax_rules = tax_repository.get_tax_rules_by_product_type(db, product_type)
        
        # If no specific rules, get default
        if not db_tax_rules:
            default_rule = tax_repository.get_default_tax_rule(db)
            if default_rule:
                db_tax_rules = [default_rule]
        
        # Calculate tax amount
        tax_amount = Decimal('0.0')
        rules_applied = []
        
        for rule in db_tax_rules:
            rule_tax = amount * Decimal(str(rule.rate))
            tax_amount += rule_tax
            
            rules_applied.append(TaxRule(
                name=rule.name,
                description=rule.description,
                rate=Decimal(str(rule.rate))
            ))
        
        total_amount = amount + tax_amount
        
        # Record the calculation
        if db_tax_rules:
            tax_repository.create_tax_calculation(
                db=db,
                user_id=user_id,
                original_amount=amount,
                tax_amount=tax_amount,
                total_amount=total_amount,
                product_type=product_type,
                rule_id=db_tax_rules[0].id,  # Primary rule
                correlation_id=correlation_id
            )
        
        # Create response object
        response = TaxCalculationResponse(
            original_amount=amount,
            tax_amount=tax_amount,
            rules_applied=rules_applied,
            total_amount=total_amount
        )
        
        # Publish tax calculated event
        await event_publisher.publish_tax_calculated(
            tax_data={
                "tax_amount": float(tax_amount),
                "rules_applied": [{"name": rule.name, "rate": float(rule.rate)} for rule in rules_applied],
                "product_type": product_type,
                "original_amount": float(amount),
                "user_id": user_id
            },
            correlation_id=correlation_id
        )
        
        return response


# Singleton instance
tax_service = TaxService()
