from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.discount import DiscountRequest, DiscountResponse
from app.services.discount_service import discount_service

router = APIRouter(tags=["discount"])


@router.post("/apply-discount", response_model=DiscountResponse)
async def apply_discount(
    request: Request,
    discount_request: DiscountRequest,
    db: Session = Depends(get_db)
):
    """
    Apply discount to an amount based on coupon, user type or amount
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
        
        # Call discount service to apply discount
        result = await discount_service.apply_discount(
            db=db,
            amount=discount_request.amount,
            coupon_code=discount_request.coupon_code,
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
    return {"status": "ok", "service": "discount-service"}
