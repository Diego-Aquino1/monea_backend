"""
Endpoints de tarjetas de crédito
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.schemas.credit_card import CreditCardCreate, CreditCardUpdate, CreditCardResponse, InstallmentPurchaseCreate
from app.utils.security import get_current_active_user
from app.services.credit_card_service import CreditCardService

router = APIRouter()


@router.get("", response_model=List[CreditCardResponse])
def get_credit_cards(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener tarjetas de crédito del usuario"""
    from app.models.credit_card import CreditCard
    
    cards = db.query(CreditCard).filter(
        CreditCard.user_id == current_user.id,
        CreditCard.is_active == True
    ).all()
    
    result = []
    for card in cards:
        card_info = CreditCardService.get_credit_card_with_calculations(
            db, current_user.id, card.id
        )
        
        response = CreditCardResponse.from_orm(card_info["credit_card"])
        response.current_balance = card_info["current_balance"]
        response.balance_at_cutoff = card_info["balance_at_cutoff"]
        response.post_cutoff_balance = card_info["post_cutoff_balance"]
        response.available_credit = card_info["available_credit"]
        response.minimum_payment = card_info["minimum_payment"]
        response.next_cutoff_date = card_info["next_cutoff_date"]
        response.next_payment_date = card_info["next_payment_date"]
        
        result.append(response)
    
    return result


@router.post("", response_model=CreditCardResponse, status_code=status.HTTP_201_CREATED)
def create_credit_card(
    card_data: CreditCardCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Crear tarjeta de crédito"""
    card = CreditCardService.create_credit_card(db, current_user.id, card_data)
    return card


@router.get("/{card_id}")
def get_credit_card(
    card_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener tarjeta con todos los cálculos"""
    return CreditCardService.get_credit_card_with_calculations(
        db, current_user.id, card_id
    )


@router.get("/{card_id}/installments")
def get_installment_purchases(
    card_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener compras a MSI de una tarjeta"""
    return CreditCardService.get_installment_purchases(
        db, current_user.id, card_id
    )


@router.get("/{card_id}/simulate-minimum")
def simulate_minimum_payment(
    card_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Simular pago mínimo"""
    return CreditCardService.simulate_minimum_payment(
        db, current_user.id, card_id
    )


@router.post("/{card_id}/pay")
def pay_credit_card(
    card_id: int,
    amount: float,
    from_account_id: int,
    payment_date: datetime = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Registrar pago de tarjeta"""
    if not payment_date:
        payment_date = datetime.now()
    
    transaction = CreditCardService.register_card_payment(
        db, current_user.id, card_id, amount, from_account_id, payment_date
    )
    
    return {"message": "Pago registrado exitosamente", "transaction_id": transaction.id}

