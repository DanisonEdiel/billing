from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.tax import TaxCalculationRequest, TaxCalculationResponse
from app.services.tax_service import tax_service

router = APIRouter(tags=["tax"])


@router.post("/calculate", response_model=TaxCalculationResponse)
async def calculate_tax(
    request: Request,
    calculation_request: TaxCalculationRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate tax for a given amount and product type
    """
    try:
        # Extract user_id from JWT token (set by middleware)
        user_id = request.state.user_id if hasattr(request.state, "user_id") else None
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
            
        # Extract correlation ID
        correlation_id = request.state.correlation_id
        
        # Call tax service to calculate tax
        result = await tax_service.calculate_tax(
            db=db,
            amount=calculation_request.amount,
            product_type=calculation_request.product_type,
            user_id=user_id,
            correlation_id=correlation_id
        )
        
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "ok", "service": "tax-service"}
