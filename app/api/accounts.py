"""
Endpoints de cuentas
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.account import Account
from app.schemas.account import AccountCreate, AccountUpdate, AccountResponse
from app.utils.security import get_current_active_user
from app.services.transaction_service import TransactionService

router = APIRouter()


@router.get("", response_model=List[AccountResponse])
def get_accounts(
    include_archived: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener cuentas del usuario"""
    query = db.query(Account).filter(Account.user_id == current_user.id)
    
    if not include_archived:
        query = query.filter(Account.is_archived == False)
    
    accounts = query.order_by(Account.display_order, Account.name).all()
    
    # Agregar balance calculado
    result = []
    for account in accounts:
        account_dict = AccountResponse.from_orm(account).dict()
        account_dict["current_balance"] = TransactionService.get_account_balance(
            db, current_user.id, account.id
        )
        result.append(account_dict)
    
    return result


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    account_data: AccountCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Crear nueva cuenta"""
    # Si es cuenta por defecto, desmarcar otras
    if account_data.is_default:
        db.query(Account).filter(
            Account.user_id == current_user.id,
            Account.is_default == True
        ).update({"is_default": False})
    
    account = Account(
        user_id=current_user.id,
        name=account_data.name,
        type=account_data.type,
        initial_balance=account_data.initial_balance,
        currency=account_data.currency,
        color=account_data.color,
        icon=account_data.icon,
        is_default=account_data.is_default,
    )
    
    db.add(account)
    db.commit()
    db.refresh(account)
    
    response = AccountResponse.from_orm(account)
    response.current_balance = account.initial_balance
    
    return response


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener cuenta específica"""
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    
    response = AccountResponse.from_orm(account)
    response.current_balance = TransactionService.get_account_balance(
        db, current_user.id, account.id
    )
    
    return response


@router.put("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: int,
    account_update: AccountUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Actualizar cuenta"""
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    
    update_data = account_update.dict(exclude_unset=True)
    
    # Si marca como default, desmarcar otras
    if update_data.get("is_default"):
        db.query(Account).filter(
            Account.user_id == current_user.id,
            Account.id != account_id,
            Account.is_default == True
        ).update({"is_default": False})
    
    for field, value in update_data.items():
        setattr(account, field, value)
    
    db.commit()
    db.refresh(account)
    
    response = AccountResponse.from_orm(account)
    response.current_balance = TransactionService.get_account_balance(
        db, current_user.id, account.id
    )
    
    return response


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Eliminar cuenta (solo si no tiene transacciones)"""
    from app.models.transaction import Transaction
    
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    
    # Verificar si tiene transacciones
    transaction_count = db.query(Transaction).filter(
        Transaction.account_id == account_id,
        Transaction.user_id == current_user.id
    ).count()
    
    if transaction_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar la cuenta porque tiene {transaction_count} transacción(es) asociada(s). Elimina primero las transacciones."
        )
    
    db.delete(account)
    db.commit()
    
    return None

