"""
Schemas de Inversiones
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from app.models.investment import InvestmentType, InvestmentTransactionType


class InvestmentBase(BaseModel):
    """Base de inversión"""
    name: str = Field(..., min_length=1, max_length=200)
    ticker: Optional[str] = None
    type: InvestmentType
    quantity: float = Field(..., ge=0)
    purchase_price: float = Field(..., gt=0)
    current_price: float = Field(..., gt=0)
    purchase_date: date


class InvestmentCreate(InvestmentBase):
    """Crear inversión"""
    broker_account: Optional[str] = None
    currency: str = "MXN"
    notes: Optional[str] = None


class InvestmentUpdate(BaseModel):
    """Actualizar inversión"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    ticker: Optional[str] = None
    quantity: Optional[float] = Field(None, ge=0)
    current_price: Optional[float] = Field(None, gt=0)
    broker_account: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class InvestmentResponse(InvestmentBase):
    """Respuesta de inversión"""
    id: int
    user_id: int
    broker_account: Optional[str]
    currency: str
    notes: Optional[str]
    is_active: bool
    last_price_update: Optional[datetime]
    created_at: datetime
    
    # Calculados
    market_value: Optional[float] = None
    cost_basis: Optional[float] = None
    unrealized_gain: Optional[float] = None
    unrealized_gain_percentage: Optional[float] = None
    realized_gain: Optional[float] = None
    total_return: Optional[float] = None
    
    class Config:
        from_attributes = True


class InvestmentTransactionCreate(BaseModel):
    """Crear transacción de inversión"""
    investment_id: int
    type: InvestmentTransactionType
    quantity: Optional[float] = Field(None, ge=0)
    price_per_unit: Optional[float] = Field(None, gt=0)
    total_amount: float
    date: date
    fees: float = 0.0
    notes: Optional[str] = None

