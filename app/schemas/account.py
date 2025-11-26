"""
Schemas de Cuentas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.account import AccountType


class AccountBase(BaseModel):
    """Base de cuenta"""
    name: str = Field(..., min_length=1, max_length=100)
    type: AccountType
    initial_balance: float = 0.0
    currency: str = "MXN"
    color: Optional[str] = "#2196F3"
    icon: Optional[str] = "account_balance_wallet"


class AccountCreate(AccountBase):
    """Crear cuenta"""
    is_default: bool = False


class AccountUpdate(BaseModel):
    """Actualizar cuenta"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = None
    icon: Optional[str] = None
    is_default: Optional[bool] = None
    is_archived: Optional[bool] = None
    exclude_from_totals: Optional[bool] = None
    display_order: Optional[int] = None


class AccountResponse(AccountBase):
    """Respuesta de cuenta"""
    id: int
    user_id: int
    is_default: bool
    is_archived: bool
    exclude_from_totals: bool
    display_order: int
    created_at: datetime
    
    # Calculado
    current_balance: Optional[float] = None
    
    class Config:
        from_attributes = True

