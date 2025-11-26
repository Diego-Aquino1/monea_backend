"""
Endpoints de alertas y notificaciones
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.alert import AlertType, AlertPriority
from app.utils.security import get_current_active_user
from app.services.alert_service import AlertService

router = APIRouter()


class AlertResponse(BaseModel):
    id: int
    user_id: int
    type: AlertType
    priority: AlertPriority
    title: str
    message: str
    is_read: bool
    is_sent: bool
    action_url: str = None
    related_transaction_id: int = None
    related_budget_id: int = None
    related_goal_id: int = None
    related_credit_card_id: int = None
    created_at: datetime
    read_at: datetime = None

    class Config:
        from_attributes = True


class AlertCreate(BaseModel):
    type: AlertType
    priority: AlertPriority = AlertPriority.MEDIUM
    title: str
    message: str
    action_url: str = None
    related_transaction_id: int = None
    related_budget_id: int = None
    related_goal_id: int = None
    related_credit_card_id: int = None


@router.get("", response_model=List[AlertResponse])
def get_alerts(
    unread_only: bool = False,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener alertas del usuario"""
    return AlertService.get_user_alerts(
        db=db,
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit
    )


@router.get("/unread-count")
def get_unread_count(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener conteo de alertas no leídas"""
    alerts = AlertService.get_user_alerts(
        db=db,
        user_id=current_user.id,
        unread_only=True,
        limit=1000
    )
    return {"count": len(alerts)}


@router.put("/{alert_id}/read", response_model=AlertResponse)
def mark_alert_as_read(
    alert_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Marcar alerta como leída"""
    alert = AlertService.mark_as_read(
        db=db,
        user_id=current_user.id,
        alert_id=alert_id
    )
    if not alert:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return alert


@router.put("/read-all", status_code=status.HTTP_204_NO_CONTENT)
def mark_all_as_read(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Marcar todas las alertas como leídas"""
    AlertService.mark_all_as_read(db=db, user_id=current_user.id)


@router.post("/generate")
def generate_alerts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generar alertas pendientes"""
    alerts = AlertService.generate_all_alerts(db=db, user_id=current_user.id)
    return {
        "generated": len(alerts),
        "alerts": [{"id": a.id, "title": a.title, "type": a.type} for a in alerts]
    }


@router.post("/check-no-transactions")
def check_no_transactions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Verificar si no hay transacciones hoy"""
    alert = AlertService.check_no_transactions_today(db=db, user_id=current_user.id)
    if alert:
        return {"alert_created": True, "alert_id": alert.id}
    return {"alert_created": False}

