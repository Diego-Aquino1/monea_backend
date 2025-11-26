"""
Schemas de Transacciones
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from app.models.transaction import TransactionType, RecurrenceFrequency


class TransactionSplitCreate(BaseModel):
    """Split de transacción"""
    category_id: int
    amount: float = Field(..., gt=0)
    notes: Optional[str] = None


class TransactionBase(BaseModel):
    """Base de transacción"""
    type: TransactionType
    amount: float = Field(..., gt=0)
    account_id: int
    category_id: Optional[int] = None
    date: datetime
    merchant: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[str] = None


class TransactionCreate(TransactionBase):
    """Crear transacción"""
    currency: str = "MXN"
    time: Optional[str] = None
    to_account_id: Optional[int] = None
    is_reimbursable: bool = False
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    location_name: Optional[str] = None
    
    # Split
    splits: Optional[List[TransactionSplitCreate]] = None
    
    # MSI
    installment_months: Optional[int] = Field(None, ge=2, le=48)


class TransactionUpdate(BaseModel):
    """Actualizar transacción"""
    type: Optional[TransactionType] = None
    amount: Optional[float] = Field(None, gt=0)
    account_id: Optional[int] = None
    category_id: Optional[int] = None
    date: Optional[datetime] = None
    merchant: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[str] = None
    is_reimbursable: Optional[bool] = None
    reimbursed: Optional[bool] = None


class TransactionResponse(TransactionBase):
    """Respuesta de transacción"""
    id: int
    user_id: int
    currency: str
    time: Optional[str]
    to_account_id: Optional[int]
    is_reimbursable: bool
    reimbursed: bool
    is_split: bool
    is_installment: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Relaciones
    account_name: Optional[str] = None
    category_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class RecurringTransactionCreate(BaseModel):
    """Crear transacción recurrente"""
    name: str = Field(..., min_length=1, max_length=200)
    type: TransactionType
    amount: float = Field(..., gt=0)
    account_id: int
    category_id: Optional[int] = None
    frequency: RecurrenceFrequency
    start_date: datetime
    end_date: Optional[datetime] = None
    day_of_month: Optional[int] = Field(None, ge=-1, le=31)
    day_of_week: Optional[int] = Field(None, ge=1, le=7)
    custom_frequency_days: Optional[int] = Field(None, ge=1)
    auto_create: bool = True
    notify_before_days: int = 2
    is_variable_amount: bool = False
    merchant: Optional[str] = None
    notes: Optional[str] = None

