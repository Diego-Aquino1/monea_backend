"""
Endpoint "¿Puedo gastar esto?"
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.utils.security import get_current_active_user
from app.services.can_spend_service import CanSpendService

router = APIRouter()


class CanSpendRequest(BaseModel):
    amount: float
    account_id: Optional[int] = None
    category_id: Optional[int] = None


class CanSpendResponse(BaseModel):
    can_spend: bool
    amount_requested: float
    current_available: float
    available_after: float
    total_liquid: float
    upcoming_obligations: float
    money_in_goals: float
    warnings: list
    impacts: list
    recommendation: str


@router.post("", response_model=CanSpendResponse)
def can_i_spend(
    request: CanSpendRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Analizar si el usuario puede gastar cierta cantidad.
    
    Considera:
    - Saldo disponible actual
    - Obligaciones próximas (tarjetas, gastos fijos)
    - Dinero apartado en metas
    - Impacto en presupuestos
    """
    result = CanSpendService.analyze_spending(
        db=db,
        user_id=current_user.id,
        amount=request.amount,
        account_id=request.account_id,
        category_id=request.category_id
    )
    
    return result


@router.get("/available-balance")
def get_available_balance(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtener saldo disponible para gastar.
    
    Saldo Disponible = Saldo Líquido - Obligaciones Próximas - Dinero en Metas
    """
    result = CanSpendService.analyze_spending(
        db=db,
        user_id=current_user.id,
        amount=0
    )
    
    return {
        "total_liquid": result["total_liquid"],
        "upcoming_obligations": result["upcoming_obligations"],
        "money_in_goals": result["money_in_goals"],
        "available_to_spend": result["current_available"]
    }

