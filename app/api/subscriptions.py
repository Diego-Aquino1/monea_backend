"""
Endpoints de suscripciones
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, date

from app.database import get_db
from app.models.user import User
from app.utils.security import get_current_active_user
from app.services.subscription_service import SubscriptionService

router = APIRouter()


class SubscriptionCreate(BaseModel):
    name: str
    amount: float
    currency: str = "PEN"
    frequency: str = "monthly"
    billing_day: Optional[int] = None
    category_id: Optional[int] = None
    account_id: Optional[int] = None
    start_date: Optional[datetime] = None
    next_billing_date: Optional[datetime] = None
    notes: Optional[str] = None
    url: Optional[str] = None
    is_investment: bool = False
    investment_id: Optional[int] = None


class SubscriptionUpdate(BaseModel):
    name: Optional[str] = None
    amount: Optional[float] = None
    frequency: Optional[str] = None
    billing_day: Optional[int] = None
    category_id: Optional[int] = None
    account_id: Optional[int] = None
    next_billing_date: Optional[datetime] = None
    notes: Optional[str] = None
    url: Optional[str] = None
    is_active: Optional[bool] = None
    is_investment: Optional[bool] = None
    investment_id: Optional[int] = None


class SubscriptionResponse(BaseModel):
    id: int
    user_id: int
    name: str
    amount: float
    currency: str
    frequency: str
    billing_day: Optional[int] = None
    category_id: Optional[int] = None
    account_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    next_billing_date: Optional[datetime] = None
    is_active: bool
    is_investment: bool = False
    investment_id: Optional[int] = None
    notes: Optional[str] = None
    url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[SubscriptionResponse])
def get_subscriptions(
    active_only: bool = True,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener suscripciones del usuario"""
    return SubscriptionService.get_subscriptions(
        db=db,
        user_id=current_user.id,
        active_only=active_only
    )


@router.post("", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_subscription(
    data: SubscriptionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Crear suscripción"""
    return SubscriptionService.create_subscription(
        db=db,
        user_id=current_user.id,
        data=data.model_dump()
    )


@router.put("/{subscription_id}", response_model=SubscriptionResponse)
def update_subscription(
    subscription_id: int,
    data: SubscriptionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Actualizar suscripción"""
    return SubscriptionService.update_subscription(
        db=db,
        user_id=current_user.id,
        subscription_id=subscription_id,
        data=data.model_dump(exclude_unset=True)
    )


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_subscription(
    subscription_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cancelar suscripción"""
    SubscriptionService.cancel_subscription(
        db=db,
        user_id=current_user.id,
        subscription_id=subscription_id
    )


@router.get("/detect")
def detect_subscriptions(
    months: int = 3,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Detectar posibles suscripciones basándose en patrones"""
    detected = SubscriptionService.detect_subscriptions(
        db=db,
        user_id=current_user.id,
        months=months
    )
    return {"detected": detected, "count": len(detected)}


@router.post("/confirm-detected")
def confirm_detected_subscription(
    detection: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Confirmar una suscripción detectada"""
    subscription = SubscriptionService.confirm_detected_subscription(
        db=db,
        user_id=current_user.id,
        detection=detection
    )
    return subscription


@router.get("/summary")
def get_subscription_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener resumen de suscripciones"""
    return SubscriptionService.get_monthly_subscription_total(
        db=db,
        user_id=current_user.id
    )


@router.get("/upcoming")
def get_upcoming_renewals(
    days: int = 7,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener renovaciones próximas"""
    return SubscriptionService.get_upcoming_renewals(
        db=db,
        user_id=current_user.id,
        days=days
    )

