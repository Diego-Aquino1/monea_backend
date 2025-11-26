"""
Endpoints de transacciones
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.transaction import TransactionType
from app.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionResponse
from app.utils.security import get_current_active_user
from app.services.transaction_service import TransactionService

router = APIRouter()


@router.get("", response_model=List[TransactionResponse])
def get_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    account_id: Optional[int] = None,
    category_id: Optional[int] = None,
    type: Optional[TransactionType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener transacciones con filtros"""
    transactions = TransactionService.get_transactions(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        account_id=account_id,
        category_id=category_id,
        type=type,
        start_date=start_date,
        end_date=end_date
    )
    
    return transactions


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Crear nueva transacción"""
    transaction = TransactionService.create_transaction(
        db=db,
        user_id=current_user.id,
        transaction_data=transaction_data
    )
    
    return transaction


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener transacción específica"""
    from app.models.transaction import Transaction
    
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Transacción no encontrada")
    
    return transaction


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    transaction_update: TransactionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Actualizar transacción"""
    transaction = TransactionService.update_transaction(
        db=db,
        user_id=current_user.id,
        transaction_id=transaction_id,
        update_data=transaction_update
    )
    
    return transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Eliminar transacción"""
    TransactionService.delete_transaction(
        db=db,
        user_id=current_user.id,
        transaction_id=transaction_id
    )

