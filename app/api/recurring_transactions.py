"""
Endpoints de transacciones recurrentes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

from app.database import get_db
from app.models.user import User
from app.models.transaction import RecurrenceFrequency, TransactionType
from app.utils.security import get_current_active_user
from app.services.recurring_service import RecurringTransactionService

router = APIRouter()


class RecurringTransactionCreate(BaseModel):
    account_id: int
    category_id: int = None
    name: str
    type: TransactionType
    amount: float
    is_variable_amount: bool = False
    frequency: RecurrenceFrequency
    custom_frequency_days: int = None
    day_of_month: int = None
    day_of_week: int = None
    start_date: datetime
    end_date: datetime = None
    auto_create: bool = True
    notify_before_days: int = 2
    merchant: str = None
    notes: str = None


class RecurringTransactionUpdate(BaseModel):
    name: str = None
    amount: float = None
    is_variable_amount: bool = None
    frequency: RecurrenceFrequency = None
    custom_frequency_days: int = None
    day_of_month: int = None
    day_of_week: int = None
    end_date: datetime = None
    auto_create: bool = None
    notify_before_days: int = None
    merchant: str = None
    notes: str = None
    is_active: bool = None


class RecurringTransactionResponse(BaseModel):
    id: int
    user_id: int
    account_id: int
    category_id: int = None
    name: str
    type: TransactionType
    amount: float
    is_variable_amount: bool
    frequency: RecurrenceFrequency
    custom_frequency_days: int = None
    day_of_month: int = None
    day_of_week: int = None
    start_date: datetime
    end_date: datetime = None
    auto_create: bool
    notify_before_days: int
    merchant: str = None
    notes: str = None
    is_active: bool
    last_created_date: datetime = None
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[RecurringTransactionResponse])
def get_recurring_transactions(
    active_only: bool = True,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener transacciones recurrentes"""
    return RecurringTransactionService.get_recurring_transactions(
        db=db,
        user_id=current_user.id,
        active_only=active_only
    )


@router.post("", response_model=RecurringTransactionResponse, status_code=status.HTTP_201_CREATED)
def create_recurring_transaction(
    data: RecurringTransactionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Crear transacción recurrente"""
    return RecurringTransactionService.create_recurring(
        db=db,
        user_id=current_user.id,
        data=data.model_dump()
    )


@router.put("/{recurring_id}", response_model=RecurringTransactionResponse)
def update_recurring_transaction(
    recurring_id: int,
    data: RecurringTransactionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Actualizar transacción recurrente"""
    return RecurringTransactionService.update_recurring(
        db=db,
        user_id=current_user.id,
        recurring_id=recurring_id,
        data=data.model_dump(exclude_unset=True)
    )


@router.delete("/{recurring_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recurring_transaction(
    recurring_id: int,
    delete_future: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Eliminar transacción recurrente"""
    RecurringTransactionService.delete_recurring(
        db=db,
        user_id=current_user.id,
        recurring_id=recurring_id,
        delete_future=delete_future
    )


@router.get("/upcoming")
def get_upcoming_recurring(
    days: int = 7,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener transacciones recurrentes próximas"""
    upcoming = RecurringTransactionService.get_upcoming_recurring(
        db=db,
        user_id=current_user.id,
        days=days
    )
    
    return [
        {
            "id": item["recurring"].id,
            "name": item["recurring"].name,
            "amount": item["recurring"].amount,
            "type": item["recurring"].type,
            "next_date": item["next_date"].isoformat(),
            "days_until": item["days_until"]
        }
        for item in upcoming
    ]


@router.post("/process", status_code=status.HTTP_200_OK)
def process_recurring_transactions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Procesar transacciones recurrentes pendientes (admin/cron)"""
    count = RecurringTransactionService.process_pending_recurring(db)
    return {"processed": count}

