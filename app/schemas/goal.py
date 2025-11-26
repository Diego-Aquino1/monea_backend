"""
Schemas de Metas Financieras
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from app.models.goal import GoalType, GoalPriority


class GoalBase(BaseModel):
    """Base de meta"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    type: GoalType
    target_amount: float = Field(..., gt=0)
    target_date: Optional[date] = None


class GoalCreate(GoalBase):
    """Crear meta"""
    initial_amount: float = Field(0.0, ge=0)
    linked_account_id: Optional[int] = None
    auto_contribution_amount: Optional[float] = None
    auto_contribution_frequency: Optional[str] = None
    priority: GoalPriority = GoalPriority.MEDIUM
    color: str = "#4CAF50"
    icon: str = "flag"


class GoalUpdate(BaseModel):
    """Actualizar meta"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    target_amount: Optional[float] = Field(None, gt=0)
    target_date: Optional[date] = None
    auto_contribution_amount: Optional[float] = None
    auto_contribution_frequency: Optional[str] = None
    priority: Optional[GoalPriority] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_archived: Optional[bool] = None


class GoalResponse(GoalBase):
    """Respuesta de meta"""
    id: int
    user_id: int
    initial_amount: float
    current_amount: float
    linked_account_id: Optional[int]
    auto_contribution_amount: Optional[float]
    auto_contribution_frequency: Optional[str]
    priority: GoalPriority
    color: str
    icon: str
    is_completed: bool
    completed_at: Optional[datetime]
    is_archived: bool
    created_at: datetime
    
    # Calculados
    progress_percentage: Optional[float] = None
    remaining_amount: Optional[float] = None
    estimated_completion_date: Optional[date] = None
    required_monthly_contribution: Optional[float] = None
    
    class Config:
        from_attributes = True


class GoalContributionCreate(BaseModel):
    """Crear aportación a meta"""
    goal_id: int
    amount: float = Field(..., gt=0)
    date: datetime
    notes: Optional[str] = None
    is_automatic: bool = False

