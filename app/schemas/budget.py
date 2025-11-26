"""
Schemas de Presupuestos
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.budget import BudgetType, BudgetPeriod


class BudgetBase(BaseModel):
    """Base de presupuesto"""
    name: str = Field(..., min_length=1, max_length=100)
    type: BudgetType
    limit_amount: float = Field(..., gt=0)
    period: BudgetPeriod
    start_day: int = Field(1, ge=1, le=31)


class BudgetCreate(BudgetBase):
    """Crear presupuesto"""
    enable_rollover: bool = False
    rollover_max_accumulation: Optional[float] = None
    alert_at_percentage: float = 80.0
    alert_on_exceed: bool = True
    
    # Filtros según tipo
    category_id: Optional[int] = None
    account_id: Optional[int] = None
    tag: Optional[str] = None


class BudgetUpdate(BaseModel):
    """Actualizar presupuesto"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    limit_amount: Optional[float] = Field(None, gt=0)
    period: Optional[BudgetPeriod] = None
    start_day: Optional[int] = Field(None, ge=1, le=31)
    enable_rollover: Optional[bool] = None
    rollover_max_accumulation: Optional[float] = None
    alert_at_percentage: Optional[float] = None
    alert_on_exceed: Optional[bool] = None
    is_active: Optional[bool] = None


class BudgetResponse(BudgetBase):
    """Respuesta de presupuesto"""
    id: int
    user_id: int
    enable_rollover: bool
    rollover_max_accumulation: Optional[float]
    current_rollover: float
    alert_at_percentage: float
    alert_on_exceed: bool
    is_active: bool
    created_at: datetime
    
    # Filtros
    category_id: Optional[int]
    account_id: Optional[int]
    tag: Optional[str]
    
    # Calculados
    spent: Optional[float] = None
    remaining: Optional[float] = None
    percentage_used: Optional[float] = None
    estimated_depletion_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True

