"""
Servicio de alertas y notificaciones
"""
from typing import List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.alert import Alert, AlertType, AlertPriority
from app.models.credit_card import CreditCard
from app.models.budget import Budget
from app.models.goal import Goal
from app.models.transaction import Transaction, TransactionType
from app.utils.calculations import get_next_cutoff_date


class AlertService:
    """Servicio para gestión de alertas"""
    
    @staticmethod
    def create_alert(db: Session, user_id: int, alert_type: AlertType,
                    title: str, message: str, priority: AlertPriority = AlertPriority.MEDIUM,
                    related_ids: dict = None) -> Alert:
        """Crear nueva alerta"""
        alert = Alert(
            user_id=user_id,
            type=alert_type,
            priority=priority,
            title=title,
            message=message,
            related_transaction_id=related_ids.get('transaction_id') if related_ids else None,
            related_budget_id=related_ids.get('budget_id') if related_ids else None,
            related_goal_id=related_ids.get('goal_id') if related_ids else None,
            related_credit_card_id=related_ids.get('credit_card_id') if related_ids else None,
        )
        
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        return alert
    
    @staticmethod
    def get_user_alerts(db: Session, user_id: int, 
                       unread_only: bool = False,
                       limit: int = 50) -> List[Alert]:
        """Obtener alertas del usuario"""
        query = db.query(Alert).filter(Alert.user_id == user_id)
        
        if unread_only:
            query = query.filter(Alert.is_read == False)
        
        return query.order_by(Alert.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def mark_as_read(db: Session, user_id: int, alert_id: int) -> Alert:
        """Marcar alerta como leída"""
        alert = db.query(Alert).filter(
            Alert.id == alert_id,
            Alert.user_id == user_id
        ).first()
        
        if alert:
            alert.is_read = True
            alert.read_at = datetime.now()
            db.commit()
            db.refresh(alert)
        
        return alert
    
    @staticmethod
    def mark_all_as_read(db: Session, user_id: int):
        """Marcar todas las alertas como leídas"""
        db.query(Alert).filter(
            Alert.user_id == user_id,
            Alert.is_read == False
        ).update({
            "is_read": True,
            "read_at": datetime.now()
        })
        db.commit()
    
    @staticmethod
    def generate_credit_card_alerts(db: Session, user_id: int):
        """Generar alertas de tarjetas de crédito"""
        today = date.today()
        
        credit_cards = db.query(CreditCard).filter(
            CreditCard.user_id == user_id,
            CreditCard.is_active == True
        ).all()
        
        alerts_created = []
        
        for card in credit_cards:
            # Alerta de fecha de corte próxima
            next_cutoff = get_next_cutoff_date(card.cutoff_day)
            days_to_cutoff = (next_cutoff - today).days
            
            if days_to_cutoff <= card.alert_days_before_cutoff:
                # Verificar que no exista alerta reciente
                existing = db.query(Alert).filter(
                    Alert.user_id == user_id,
                    Alert.type == AlertType.CREDIT_CARD_CUTOFF,
                    Alert.related_credit_card_id == card.id,
                    Alert.created_at >= datetime.now() - timedelta(days=1)
                ).first()
                
                if not existing:
                    alert = AlertService.create_alert(
                        db, user_id,
                        AlertType.CREDIT_CARD_CUTOFF,
                        f"Corte próximo: {card.card_name}",
                        f"Tu tarjeta {card.card_name} cortará en {days_to_cutoff} días ({next_cutoff.strftime('%d/%m')})",
                        AlertPriority.MEDIUM,
                        {"credit_card_id": card.id}
                    )
                    alerts_created.append(alert)
            
            # Alerta de fecha límite de pago
            next_payment = get_next_cutoff_date(card.payment_due_day)
            days_to_payment = (next_payment - today).days
            
            if days_to_payment <= card.alert_days_before_payment:
                existing = db.query(Alert).filter(
                    Alert.user_id == user_id,
                    Alert.type == AlertType.CREDIT_CARD_PAYMENT,
                    Alert.related_credit_card_id == card.id,
                    Alert.created_at >= datetime.now() - timedelta(days=1)
                ).first()
                
                if not existing:
                    alert = AlertService.create_alert(
                        db, user_id,
                        AlertType.CREDIT_CARD_PAYMENT,
                        f"Pago próximo: {card.card_name}",
                        f"Tu pago de {card.card_name} vence en {days_to_payment} días ({next_payment.strftime('%d/%m')})",
                        AlertPriority.HIGH,
                        {"credit_card_id": card.id}
                    )
                    alerts_created.append(alert)
        
        return alerts_created
    
    @staticmethod
    def generate_budget_alerts(db: Session, user_id: int):
        """Generar alertas de presupuestos"""
        from app.services.budget_service import BudgetService
        
        budgets = db.query(Budget).filter(
            Budget.user_id == user_id,
            Budget.is_active == True
        ).all()
        
        alerts_created = []
        
        for budget in budgets:
            budget_info = BudgetService.get_budget_with_calculations(db, user_id, budget.id)
            percentage = budget_info["percentage_used"]
            
            # Alerta al alcanzar umbral
            if percentage >= budget.alert_at_percentage and percentage < 100:
                existing = db.query(Alert).filter(
                    Alert.user_id == user_id,
                    Alert.type == AlertType.BUDGET_WARNING,
                    Alert.related_budget_id == budget.id,
                    Alert.created_at >= datetime.now() - timedelta(days=1)
                ).first()
                
                if not existing:
                    alert = AlertService.create_alert(
                        db, user_id,
                        AlertType.BUDGET_WARNING,
                        f"Presupuesto al {int(percentage)}%",
                        f"Tu presupuesto '{budget.name}' está al {int(percentage)}% de uso",
                        AlertPriority.MEDIUM,
                        {"budget_id": budget.id}
                    )
                    alerts_created.append(alert)
            
            # Alerta si excede
            elif percentage >= 100 and budget.alert_on_exceed:
                existing = db.query(Alert).filter(
                    Alert.user_id == user_id,
                    Alert.type == AlertType.BUDGET_EXCEEDED,
                    Alert.related_budget_id == budget.id,
                    Alert.created_at >= datetime.now() - timedelta(days=1)
                ).first()
                
                if not existing:
                    alert = AlertService.create_alert(
                        db, user_id,
                        AlertType.BUDGET_EXCEEDED,
                        f"Presupuesto excedido",
                        f"Tu presupuesto '{budget.name}' ha sido excedido ({int(percentage)}%)",
                        AlertPriority.HIGH,
                        {"budget_id": budget.id}
                    )
                    alerts_created.append(alert)
        
        return alerts_created
    
    @staticmethod
    def generate_goal_alerts(db: Session, user_id: int):
        """Generar alertas de metas completadas"""
        goals = db.query(Goal).filter(
            Goal.user_id == user_id,
            Goal.is_completed == True,
            Goal.is_archived == False
        ).all()
        
        alerts_created = []
        
        for goal in goals:
            existing = db.query(Alert).filter(
                Alert.user_id == user_id,
                Alert.type == AlertType.GOAL_COMPLETED,
                Alert.related_goal_id == goal.id
            ).first()
            
            if not existing:
                alert = AlertService.create_alert(
                    db, user_id,
                    AlertType.GOAL_COMPLETED,
                    f"¡Meta completada!",
                    f"Felicidades, completaste tu meta '{goal.name}'",
                    AlertPriority.LOW,
                    {"goal_id": goal.id}
                )
                alerts_created.append(alert)
        
        return alerts_created
    
    @staticmethod
    def check_no_transactions_today(db: Session, user_id: int) -> Optional[Alert]:
        """Verificar si no hay transacciones hoy"""
        today_start = datetime.combine(date.today(), datetime.min.time())
        today_end = datetime.combine(date.today(), datetime.max.time())
        
        transactions_today = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.date >= today_start,
            Transaction.date <= today_end
        ).count()
        
        if transactions_today == 0:
            existing = db.query(Alert).filter(
                Alert.user_id == user_id,
                Alert.type == AlertType.NO_TRANSACTIONS_TODAY,
                Alert.created_at >= today_start
            ).first()
            
            if not existing:
                return AlertService.create_alert(
                    db, user_id,
                    AlertType.NO_TRANSACTIONS_TODAY,
                    "¿Día sin gastos?",
                    "No has registrado transacciones hoy. ¿Todo bien o se te olvidó algo?",
                    AlertPriority.LOW
                )
        
        return None
    
    @staticmethod
    def generate_all_alerts(db: Session, user_id: int) -> List[Alert]:
        """Generar todas las alertas pendientes"""
        alerts = []
        
        alerts.extend(AlertService.generate_credit_card_alerts(db, user_id))
        alerts.extend(AlertService.generate_budget_alerts(db, user_id))
        alerts.extend(AlertService.generate_goal_alerts(db, user_id))
        
        return alerts

