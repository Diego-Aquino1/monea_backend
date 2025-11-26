"""
Endpoints de análisis y reportes
"""
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from datetime import date

from app.database import get_db
from app.models.user import User
from app.utils.security import get_current_active_user
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/dashboard")
def get_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener resumen para dashboard"""
    return AnalyticsService.get_dashboard_summary(db, current_user.id)


@router.get("/expenses-by-category")
def get_expenses_by_category(
    start_date: date = Query(...),
    end_date: date = Query(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener gastos por categoría"""
    return AnalyticsService.get_expense_by_category(
        db, current_user.id, start_date, end_date
    )


@router.get("/monthly-trend")
def get_monthly_trend(
    months: int = Query(6, ge=1, le=24),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener tendencia mensual"""
    return AnalyticsService.get_monthly_trend(db, current_user.id, months)


@router.get("/small-expenses")
def detect_small_expenses(
    threshold: float = Query(100, gt=0),
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Detectar gastos hormiga"""
    return AnalyticsService.detect_small_expenses(
        db, current_user.id, threshold, days
    )


@router.get("/net-worth")
def get_net_worth(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener valor neto"""
    return AnalyticsService.get_net_worth(db, current_user.id)


@router.get("/monthly-report/{year}/{month}")
def get_monthly_report(
    year: int = Path(..., ge=2000, le=2100),
    month: int = Path(..., ge=1, le=12),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener reporte mensual completo"""
    return AnalyticsService.get_monthly_report(db, current_user.id, year, month)