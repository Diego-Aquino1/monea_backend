"""
Endpoints de inversiones
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.investment import Investment
from app.schemas.investment import InvestmentCreate, InvestmentUpdate, InvestmentResponse
from app.utils.security import get_current_active_user
from app.utils.calculations import calculate_investment_return

router = APIRouter()


@router.get("", response_model=List[InvestmentResponse])
def get_investments(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener inversiones con cálculos"""
    investments = db.query(Investment).filter(
        Investment.user_id == current_user.id,
        Investment.is_active == True
    ).all()
    
    result = []
    for inv in investments:
        response = InvestmentResponse.from_orm(inv)
        
        # Calcular valores
        response.market_value = inv.quantity * inv.current_price
        response.cost_basis = inv.quantity * inv.purchase_price
        response.unrealized_gain, response.unrealized_gain_percentage = calculate_investment_return(
            inv.purchase_price, inv.current_price, inv.quantity
        )
        
        result.append(response)
    
    return result


@router.post("", response_model=InvestmentResponse, status_code=status.HTTP_201_CREATED)
def create_investment(
    investment_data: InvestmentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Crear inversión"""
    investment = Investment(
        user_id=current_user.id,
        **investment_data.dict()
    )
    
    db.add(investment)
    db.commit()
    db.refresh(investment)
    
    return investment


@router.get("/{investment_id}", response_model=InvestmentResponse)
def get_investment(
    investment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener inversión específica"""
    investment = db.query(Investment).filter(
        Investment.id == investment_id,
        Investment.user_id == current_user.id
    ).first()
    
    if not investment:
        raise HTTPException(status_code=404, detail="Inversión no encontrada")
    
    response = InvestmentResponse.from_orm(investment)
    response.market_value = investment.quantity * investment.current_price
    response.cost_basis = investment.quantity * investment.purchase_price
    response.unrealized_gain, response.unrealized_gain_percentage = calculate_investment_return(
        investment.purchase_price, investment.current_price, investment.quantity
    )
    
    return response


@router.put("/{investment_id}", response_model=InvestmentResponse)
def update_investment(
    investment_id: int,
    investment_update: InvestmentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Actualizar inversión"""
    investment = db.query(Investment).filter(
        Investment.id == investment_id,
        Investment.user_id == current_user.id
    ).first()
    
    if not investment:
        raise HTTPException(status_code=404, detail="Inversión no encontrada")
    
    update_data = investment_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(investment, field, value)
    
    db.commit()
    db.refresh(investment)
    
    return investment


@router.delete("/{investment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_investment(
    investment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Eliminar inversión"""
    investment = db.query(Investment).filter(
        Investment.id == investment_id,
        Investment.user_id == current_user.id
    ).first()
    
    if not investment:
        raise HTTPException(status_code=404, detail="Inversión no encontrada")
    
    # Marcar como inactiva en lugar de eliminar (soft delete)
    # Para mantener historial de transacciones de inversión
    investment.is_active = False
    db.commit()
    
    return None

