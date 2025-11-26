"""
Endpoints de presupuestos
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.budget import Budget
from app.schemas.budget import BudgetCreate, BudgetUpdate, BudgetResponse
from app.utils.security import get_current_active_user
from app.services.budget_service import BudgetService

router = APIRouter()


@router.get("")
def get_budgets(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener presupuestos con cálculos"""
    budgets = db.query(Budget).filter(
        Budget.user_id == current_user.id,
        Budget.is_active == True
    ).all()
    
    result = []
    for budget in budgets:
        budget_info = BudgetService.get_budget_with_calculations(
            db, current_user.id, budget.id
        )
        result.append(budget_info)
    
    return result


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(
    budget_data: BudgetCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Crear presupuesto"""
    budget = BudgetService.create_budget(db, current_user.id, budget_data)
    return budget


@router.get("/{budget_id}")
def get_budget(
    budget_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener presupuesto con cálculos"""
    return BudgetService.get_budget_with_calculations(
        db, current_user.id, budget_id
    )


@router.put("/{budget_id}", response_model=BudgetResponse)
def update_budget(
    budget_id: int,
    budget_update: BudgetUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Actualizar presupuesto"""
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()
    
    if not budget:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    
    update_data = budget_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(budget, field, value)
    
    db.commit()
    db.refresh(budget)
    
    return budget

