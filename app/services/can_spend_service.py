"""
Servicio "¿Puedo gastar esto?"
"""
from typing import Dict, List
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.budget import Budget
from app.models.goal import Goal
from app.models.credit_card import CreditCard
from app.models.transaction import Transaction, TransactionType
from app.services.transaction_service import TransactionService
from app.services.budget_service import BudgetService
from app.services.goal_service import GoalService
from app.services.credit_card_service import CreditCardService
from app.utils.calculations import get_next_cutoff_date


class CanSpendService:
    """Servicio para análisis de viabilidad de gasto"""
    
    @staticmethod
    def analyze_spending(db: Session, user_id: int, amount: float, 
                        account_id: int = None, category_id: int = None) -> Dict:
        """
        Analizar si el usuario puede gastar cierta cantidad
        
        Retorna:
        - can_spend: bool
        - available_after: float
        - warnings: list
        - impacts: list
        - recommendation: str
        """
        warnings = []
        impacts = []
        
        # 1. Calcular saldo disponible actual
        accounts = db.query(Account).filter(
            Account.user_id == user_id,
            Account.is_archived == False,
            Account.type.in_(["cash", "debit", "savings"])
        ).all()
        
        total_liquid = sum(
            TransactionService.get_account_balance(db, user_id, acc.id)
            for acc in accounts
        )
        
        # 2. Calcular obligaciones próximas (15 días)
        upcoming_obligations = CanSpendService._get_upcoming_obligations(db, user_id)
        
        # 3. Calcular dinero apartado en metas
        goals = db.query(Goal).filter(
            Goal.user_id == user_id,
            Goal.is_completed == False,
            Goal.is_archived == False
        ).all()
        money_in_goals = sum(g.current_amount for g in goals)
        
        # 4. Calcular saldo disponible real
        available = total_liquid - upcoming_obligations - money_in_goals
        available_after = available - amount
        
        can_spend = available_after >= 0
        
        # 5. Verificar impacto en presupuestos
        if category_id:
            budget_impact = CanSpendService._check_budget_impact(
                db, user_id, category_id, amount
            )
            if budget_impact:
                impacts.append(budget_impact)
                if budget_impact.get("will_exceed"):
                    warnings.append(f"Excederás tu presupuesto de {budget_impact['budget_name']}")
        
        # 6. Verificar impacto en metas
        if available_after < 0:
            affected_goals = CanSpendService._get_affected_goals(
                db, user_id, abs(available_after)
            )
            if affected_goals:
                warnings.append(f"Esto podría afectar tus metas de ahorro")
                impacts.extend(affected_goals)
        
        # 7. Verificar si afecta pagos de tarjetas
        if account_id:
            card_impact = CanSpendService._check_credit_card_impact(
                db, user_id, account_id, amount
            )
            if card_impact:
                warnings.append(card_impact["message"])
                impacts.append(card_impact)
        
        # 8. Generar recomendación
        recommendation = CanSpendService._generate_recommendation(
            can_spend, available, available_after, amount, warnings
        )
        
        return {
            "can_spend": can_spend,
            "amount_requested": amount,
            "current_available": available,
            "available_after": available_after,
            "total_liquid": total_liquid,
            "upcoming_obligations": upcoming_obligations,
            "money_in_goals": money_in_goals,
            "warnings": warnings,
            "impacts": impacts,
            "recommendation": recommendation,
        }
    
    @staticmethod
    def _get_upcoming_obligations(db: Session, user_id: int, days: int = 15) -> float:
        """Obtener obligaciones próximas"""
        today = date.today()
        end_date = today + timedelta(days=days)
        total = 0.0
        
        # Saldos al corte de tarjetas
        credit_cards = db.query(CreditCard).filter(
            CreditCard.user_id == user_id,
            CreditCard.is_active == True
        ).all()
        
        for card in credit_cards:
            next_payment = get_next_cutoff_date(card.payment_due_day)
            if today <= next_payment <= end_date:
                card_info = CreditCardService.get_credit_card_with_calculations(
                    db, user_id, card.id
                )
                total += card_info.get("balance_at_cutoff", 0)
        
        # TODO: Agregar gastos fijos programados
        
        return total
    
    @staticmethod
    def _check_budget_impact(db: Session, user_id: int, 
                            category_id: int, amount: float) -> Dict:
        """Verificar impacto en presupuestos"""
        from app.models.budget import BudgetType
        
        # Buscar presupuesto de la categoría
        budget = db.query(Budget).filter(
            Budget.user_id == user_id,
            Budget.category_id == category_id,
            Budget.is_active == True
        ).first()
        
        if not budget:
            return None
        
        budget_info = BudgetService.get_budget_with_calculations(db, user_id, budget.id)
        
        current_spent = budget_info["spent"]
        limit = budget_info["limit"]
        new_spent = current_spent + amount
        new_percentage = (new_spent / limit) * 100 if limit > 0 else 0
        
        return {
            "type": "budget",
            "budget_id": budget.id,
            "budget_name": budget.name,
            "current_spent": current_spent,
            "limit": limit,
            "new_spent": new_spent,
            "new_percentage": new_percentage,
            "will_exceed": new_percentage > 100,
        }
    
    @staticmethod
    def _get_affected_goals(db: Session, user_id: int, deficit: float) -> List[Dict]:
        """Obtener metas que podrían verse afectadas"""
        goals = db.query(Goal).filter(
            Goal.user_id == user_id,
            Goal.is_completed == False,
            Goal.is_archived == False
        ).order_by(Goal.current_amount.desc()).all()
        
        affected = []
        remaining_deficit = deficit
        
        for goal in goals:
            if remaining_deficit <= 0:
                break
            
            impact = min(remaining_deficit, goal.current_amount)
            if impact > 0:
                affected.append({
                    "type": "goal",
                    "goal_id": goal.id,
                    "goal_name": goal.name,
                    "current_amount": goal.current_amount,
                    "potential_impact": impact,
                    "delay_days": int((impact / (goal.auto_contribution_amount or 1000)) * 30)
                })
                remaining_deficit -= impact
        
        return affected
    
    @staticmethod
    def _check_credit_card_impact(db: Session, user_id: int, 
                                  account_id: int, amount: float) -> Dict:
        """Verificar si el gasto afecta pagos de tarjetas"""
        # Verificar si la cuenta tiene fondos suficientes para pagos próximos
        account = db.query(Account).filter(
            Account.id == account_id,
            Account.user_id == user_id
        ).first()
        
        if not account or account.type not in ["debit", "savings"]:
            return None
        
        current_balance = TransactionService.get_account_balance(db, user_id, account_id)
        balance_after = current_balance - amount
        
        # Verificar pagos próximos de tarjetas
        credit_cards = db.query(CreditCard).filter(
            CreditCard.user_id == user_id,
            CreditCard.is_active == True
        ).all()
        
        upcoming_payments = 0
        for card in credit_cards:
            next_payment = get_next_cutoff_date(card.payment_due_day)
            if (next_payment - date.today()).days <= 15:
                card_info = CreditCardService.get_credit_card_with_calculations(
                    db, user_id, card.id
                )
                upcoming_payments += card_info.get("balance_at_cutoff", 0)
        
        if upcoming_payments > 0 and balance_after < upcoming_payments:
            return {
                "type": "credit_card_payment",
                "message": f"Podrías quedarte sin fondos para tus pagos de tarjeta (${upcoming_payments:,.2f})",
                "upcoming_payments": upcoming_payments,
                "balance_after": balance_after,
                "deficit": upcoming_payments - balance_after
            }
        
        return None
    
    @staticmethod
    def _generate_recommendation(can_spend: bool, available: float, 
                                 available_after: float, amount: float,
                                 warnings: List[str]) -> str:
        """Generar recomendación de texto"""
        if can_spend and not warnings:
            return f"✅ Sí, puedes gastar ${amount:,.2f}. Tu saldo disponible quedará en ${available_after:,.2f}."
        
        elif can_spend and warnings:
            return f"⚠️ Puedes gastar ${amount:,.2f}, pero ten en cuenta: {'; '.join(warnings)}"
        
        else:
            deficit = abs(available_after)
            return f"❌ No es recomendable. Te faltarían ${deficit:,.2f}. Considera reducir el gasto o esperar a tener más fondos."

