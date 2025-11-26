"""
Servicio de presupuestos
"""
from typing import List, Dict
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.budget import Budget, BudgetType, BudgetPeriod
from app.models.transaction import Transaction, TransactionType
from app.schemas.budget import BudgetCreate, BudgetUpdate
from app.utils.calculations import calculate_budget_progress, estimate_budget_depletion_date
from dateutil.relativedelta import relativedelta


class BudgetService:
    """Servicio para gestión de presupuestos"""
    
    @staticmethod
    def create_budget(db: Session, user_id: int, budget_data: BudgetCreate) -> Budget:
        """Crear presupuesto"""
        budget = Budget(
            user_id=user_id,
            name=budget_data.name,
            type=budget_data.type,
            limit_amount=budget_data.limit_amount,
            period=budget_data.period,
            start_day=budget_data.start_day,
            enable_rollover=budget_data.enable_rollover,
            rollover_max_accumulation=budget_data.rollover_max_accumulation,
            alert_at_percentage=budget_data.alert_at_percentage,
            alert_on_exceed=budget_data.alert_on_exceed,
            category_id=budget_data.category_id,
            account_id=budget_data.account_id,
            tag=budget_data.tag,
        )
        
        db.add(budget)
        db.commit()
        db.refresh(budget)
        
        return budget
    
    @staticmethod
    def get_budget_with_calculations(db: Session, user_id: int, budget_id: int) -> Dict:
        """Obtener presupuesto con cálculos"""
        budget = db.query(Budget).filter(
            Budget.id == budget_id,
            Budget.user_id == user_id
        ).first()
        
        if not budget:
            raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
        
        # Calcular periodo actual
        start_date, end_date = BudgetService._get_period_dates(budget)
        
        # Obtener transacciones que aplican a este presupuesto
        transactions = BudgetService._get_budget_transactions(db, user_id, budget, start_date, end_date)
        
        # Calcular gasto
        spent = sum(t.amount for t in transactions)
        
        # Aplicar rollover si está habilitado
        effective_limit = budget.limit_amount
        if budget.enable_rollover and budget.current_rollover > 0:
            effective_limit += budget.current_rollover
            
            if budget.rollover_max_accumulation:
                effective_limit = min(effective_limit, 
                                    budget.limit_amount + budget.rollover_max_accumulation)
        
        remaining = effective_limit - spent
        percentage_used = calculate_budget_progress(spent, effective_limit)
        
        # Estimar fecha de agotamiento
        days_elapsed = (datetime.now().date() - start_date).days + 1
        total_days = (end_date - start_date).days + 1
        
        depletion_date = None
        if spent > 0 and remaining > 0:
            depletion_date = estimate_budget_depletion_date(
                spent, effective_limit, days_elapsed, total_days
            )
        
        return {
            "budget": budget,
            "period_start": start_date,
            "period_end": end_date,
            "spent": spent,
            "limit": effective_limit,
            "remaining": remaining,
            "percentage_used": percentage_used,
            "estimated_depletion_date": depletion_date,
            "days_remaining": (end_date - datetime.now().date()).days,
            "status": BudgetService._get_budget_status(percentage_used),
        }
    
    @staticmethod
    def _get_period_dates(budget: Budget) -> tuple:
        """Obtener fechas de inicio y fin del periodo actual"""
        today = date.today()
        
        if budget.period == BudgetPeriod.WEEKLY:
            # Última ocurrencia del día de inicio
            days_since_start = (today.weekday() - budget.start_day) % 7
            start_date = today - timedelta(days=days_since_start)
            end_date = start_date + timedelta(days=6)
        
        elif budget.period == BudgetPeriod.BIWEEKLY:
            # Calcular quincenal
            if today.day >= budget.start_day:
                start_date = date(today.year, today.month, budget.start_day)
            else:
                prev_month = today - relativedelta(months=1)
                start_date = date(prev_month.year, prev_month.month, budget.start_day)
            
            end_date = start_date + timedelta(days=13)
        
        elif budget.period == BudgetPeriod.MONTHLY:
            # Mensual
            if today.day >= budget.start_day:
                start_date = date(today.year, today.month, budget.start_day)
            else:
                prev_month = today - relativedelta(months=1)
                start_date = date(prev_month.year, prev_month.month, budget.start_day)
            
            end_date = start_date + relativedelta(months=1) - timedelta(days=1)
        
        elif budget.period == BudgetPeriod.ANNUAL:
            # Anual
            year = today.year
            if today < date(year, 1, budget.start_day):
                year -= 1
            
            start_date = date(year, 1, budget.start_day)
            end_date = date(year + 1, 1, budget.start_day) - timedelta(days=1)
        
        else:
            # Por defecto, mensual
            start_date = date(today.year, today.month, 1)
            end_date = start_date + relativedelta(months=1) - timedelta(days=1)
        
        return start_date, end_date
    
    @staticmethod
    def _get_budget_transactions(db: Session, user_id: int, budget: Budget,
                                 start_date: date, end_date: date) -> List[Transaction]:
        """Obtener transacciones que aplican a un presupuesto"""
        query = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.date >= start_date,
            Transaction.date <= end_date
        )
        
        if budget.type == BudgetType.CATEGORY:
            query = query.filter(Transaction.category_id == budget.category_id)
        
        elif budget.type == BudgetType.ACCOUNT:
            query = query.filter(Transaction.account_id == budget.account_id)
        
        elif budget.type == BudgetType.TAG:
            # Buscar en tags (campo JSON string)
            query = query.filter(Transaction.tags.contains(budget.tag))
        
        # BudgetType.GLOBAL incluye todas las transacciones
        
        return query.all()
    
    @staticmethod
    def _get_budget_status(percentage: float) -> str:
        """Determinar estado del presupuesto según porcentaje"""
        if percentage <= 70:
            return "safe"
        elif percentage <= 90:
            return "warning"
        elif percentage <= 100:
            return "critical"
        else:
            return "exceeded"
    
    @staticmethod
    def process_period_end(db: Session, budget: Budget):
        """Procesar fin de periodo (para rollover)"""
        if not budget.enable_rollover:
            return
        
        # Calcular sobrante
        info = BudgetService.get_budget_with_calculations(db, budget.user_id, budget.id)
        remaining = info["remaining"]
        
        if remaining > 0:
            # Acumular al rollover
            budget.current_rollover += remaining
            
            # Aplicar límite si existe
            if budget.rollover_max_accumulation:
                budget.current_rollover = min(
                    budget.current_rollover,
                    budget.rollover_max_accumulation
                )
        else:
            # Si se excedió, resetear rollover
            budget.current_rollover = 0
        
        db.commit()

