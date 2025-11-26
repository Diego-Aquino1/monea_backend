"""
Schemas de Tarjetas de Crédito
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date


class CreditCardBase(BaseModel):
    """Base de tarjeta de crédito"""
    card_name: str = Field(..., min_length=1, max_length=100)
    last_four_digits: Optional[str] = Field(None, min_length=4, max_length=4)
    credit_limit: float = Field(..., gt=0)
    cutoff_day: int = Field(..., ge=1, le=28)
    payment_due_day: int = Field(..., ge=1, le=31)
    annual_interest_rate: float = Field(0.0, ge=0, le=200)
    minimum_payment_percentage: float = Field(5.0, ge=0, le=100)


class CreditCardCreate(CreditCardBase):
    """Crear tarjeta de crédito"""
    account_id: int
    color: Optional[str] = "#FF5722"
    icon: Optional[str] = "credit_card"


class CreditCardUpdate(BaseModel):
    """Actualizar tarjeta de crédito"""
    card_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_four_digits: Optional[str] = Field(None, min_length=4, max_length=4)
    credit_limit: Optional[float] = Field(None, gt=0)
    cutoff_day: Optional[int] = Field(None, ge=1, le=28)
    payment_due_day: Optional[int] = Field(None, ge=1, le=31)
    annual_interest_rate: Optional[float] = Field(None, ge=0, le=200)
    minimum_payment_percentage: Optional[float] = Field(None, ge=0, le=100)
    color: Optional[str] = None
    icon: Optional[str] = None


class CreditCardResponse(CreditCardBase):
    """Respuesta de tarjeta de crédito"""
    id: int
    account_id: int
    user_id: int
    color: str
    icon: str
    is_active: bool
    created_at: datetime
    
    # Calculados
    current_balance: Optional[float] = None
    balance_at_cutoff: Optional[float] = None
    post_cutoff_balance: Optional[float] = None
    available_credit: Optional[float] = None
    minimum_payment: Optional[float] = None
    next_cutoff_date: Optional[date] = None
    next_payment_date: Optional[date] = None
    
    class Config:
        from_attributes = True


class InstallmentPurchaseCreate(BaseModel):
    """Crear compra a MSI"""
    credit_card_id: int
    category_id: Optional[int] = None
    description: str = Field(..., min_length=1, max_length=200)
    merchant: Optional[str] = None
    total_amount: float = Field(..., gt=0)
    number_of_installments: int = Field(..., ge=2, le=48)
    purchase_date: date


class InstallmentPurchaseResponse(BaseModel):
    """Respuesta de compra a MSI"""
    id: int
    credit_card_id: int
    description: str
    merchant: Optional[str]
    total_amount: float
    number_of_installments: int
    installment_amount: float
    purchase_date: date
    first_installment_date: date
    is_active: bool
    completed: bool
    
    # Calculados
    installments_paid: Optional[int] = None
    installments_remaining: Optional[int] = None
    amount_paid: Optional[float] = None
    amount_remaining: Optional[float] = None
    
    class Config:
        from_attributes = True

