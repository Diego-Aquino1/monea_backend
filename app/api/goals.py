"""
Endpoints de metas financieras
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.goal import Goal
from app.schemas.goal import GoalCreate, GoalUpdate, GoalResponse, GoalContributionCreate
from app.utils.security import get_current_active_user
from app.services.goal_service import GoalService

router = APIRouter()


@router.get("")
def get_goals(
    include_completed: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener metas con cálculos"""
    query = db.query(Goal).filter(
        Goal.user_id == current_user.id,
        Goal.is_archived == False
    )
    
    if not include_completed:
        query = query.filter(Goal.is_completed == False)
    
    goals = query.all()
    
    result = []
    for goal in goals:
        goal_info = GoalService.get_goal_with_calculations(
            db, current_user.id, goal.id
        )
        result.append(goal_info)
    
    return result


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(
    goal_data: GoalCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Crear meta"""
    goal = GoalService.create_goal(db, current_user.id, goal_data)
    return goal


@router.get("/{goal_id}")
def get_goal(
    goal_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener meta con cálculos"""
    return GoalService.get_goal_with_calculations(
        db, current_user.id, goal_id
    )


@router.post("/{goal_id}/contribute")
def add_contribution(
    contribution_data: GoalContributionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Agregar contribución a meta"""
    contribution = GoalService.add_contribution(
        db, current_user.id, contribution_data
    )
    
    return {"message": "Contribución agregada", "contribution_id": contribution.id}


@router.post("/{goal_id}/withdraw")
def withdraw_from_goal(
    goal_id: int,
    amount: float,
    notes: str = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Retirar de meta"""
    goal = GoalService.withdraw_from_goal(
        db, current_user.id, goal_id, amount, notes
    )
    
    return {"message": "Retiro registrado", "goal": goal}

