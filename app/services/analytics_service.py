"""
Servicio de análisis y reportes
"""
from typing import List, Dict
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from collections import defaultdict

from app.models.transaction import Transaction, TransactionType
from app.models.category import Category
from app.models.account import Account
from app.models.investment import Investment
from app.models.budget import Budget
from app.models.goal import Goal
from app.utils.calculations import calculate_net_worth, calculate_investment_return


class AnalyticsService:
    """Servicio para análisis y reportes financieros"""
    
    @staticmethod
    def get_dashboard_summary(db: Session, user_id: int) -> Dict:
        """Obtener resumen para dashboard"""
        today = date.today()
        first_day_month = date(today.year, today.month, 1)
        
        # Ingresos del mes
        incomes = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.INCOME,
            Transaction.date >= first_day_month
        ).scalar() or 0
        
        # Gastos del mes
        expenses = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.date >= first_day_month
        ).scalar() or 0
        
        # Balance del mes
        balance = incomes - expenses
        
        # Saldo total de cuentas líquidas
        accounts = db.query(Account).filter(
            Account.user_id == user_id,
            Account.is_archived == False,
            Account.type.in_(["cash", "debit", "savings"])
        ).all()
        
        # Aquí deberíamos calcular el saldo de cada cuenta,
        # por simplicidad usamos el servicio de transacciones
        from app.services.transaction_service import TransactionService
        total_balance = sum(
            TransactionService.get_account_balance(db, user_id, acc.id)
            for acc in accounts
        )
        
        # Top 5 categorías del mes
        top_categories = db.query(
            Category.name,
            func.sum(Transaction.amount).label("total")
        ).join(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.date >= first_day_month
        ).group_by(Category.id).order_by(func.sum(Transaction.amount).desc()).limit(5).all()
        
        return {
            "month_incomes": incomes,
            "month_expenses": expenses,
            "month_balance": balance,
            "total_balance": total_balance,
            "top_categories": [
                {"name": cat[0], "amount": cat[1]}
                for cat in top_categories
            ],
        }
    
    @staticmethod
    def get_expense_by_category(db: Session, user_id: int, 
                                start_date: date, end_date: date) -> List[Dict]:
        """Obtener gastos agrupados por categoría"""
        results = db.query(
            Category.id,
            Category.name,
            Category.color,
            Category.icon,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count")
        ).join(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).group_by(Category.id).order_by(func.sum(Transaction.amount).desc()).all()
        
        total = sum(r.total for r in results)
        
        return [
            {
                "category_id": r.id,
                "category_name": r.name,
                "color": r.color,
                "icon": r.icon,
                "amount": r.total,
                "transaction_count": r.count,
                "percentage": (r.total / total * 100) if total > 0 else 0
            }
            for r in results
        ]
    
    @staticmethod
    def get_monthly_trend(db: Session, user_id: int, months: int = 6) -> List[Dict]:
        """Obtener tendencia mensual de ingresos y gastos"""
        end_date = date.today()
        start_date = end_date - timedelta(days=months * 30)
        
        # Agrupar por mes
        results = db.query(
            extract("year", Transaction.date).label("year"),
            extract("month", Transaction.date).label("month"),
            Transaction.type,
            func.sum(Transaction.amount).label("total")
        ).filter(
            Transaction.user_id == user_id,
            Transaction.date >= start_date,
            Transaction.type.in_([TransactionType.INCOME, TransactionType.EXPENSE])
        ).group_by(
            extract("year", Transaction.date),
            extract("month", Transaction.date),
            Transaction.type
        ).all()
        
        # Organizar por mes
        by_month = defaultdict(lambda: {"incomes": 0, "expenses": 0})
        
        for r in results:
            month_key = f"{int(r.year)}-{int(r.month):02d}"
            if r.type == TransactionType.INCOME:
                by_month[month_key]["incomes"] = r.total
            else:
                by_month[month_key]["expenses"] = r.total
        
        # Convertir a lista ordenada
        result = []
        for month_key in sorted(by_month.keys()):
            data = by_month[month_key]
            result.append({
                "month": month_key,
                "incomes": data["incomes"],
                "expenses": data["expenses"],
                "balance": data["incomes"] - data["expenses"]
            })
        
        return result
    
    @staticmethod
    def detect_small_expenses(db: Session, user_id: int, 
                             threshold: float = 100, days: int = 30) -> Dict:
        """Detectar gastos hormiga (pequeños gastos frecuentes)"""
        start_date = date.today() - timedelta(days=days)
        
        small_expenses = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.amount <= threshold,
            Transaction.date >= start_date
        ).all()
        
        # Agrupar por categoría
        by_category = defaultdict(lambda: {"count": 0, "total": 0})
        
        for exp in small_expenses:
            if exp.category_id:
                category = db.query(Category).get(exp.category_id)
                cat_name = category.name if category else "Sin categoría"
            else:
                cat_name = "Sin categoría"
            
            by_category[cat_name]["count"] += 1
            by_category[cat_name]["total"] += exp.amount
        
        total_amount = sum(exp.amount for exp in small_expenses)
        total_count = len(small_expenses)
        
        return {
            "period_days": days,
            "threshold": threshold,
            "total_small_expenses": total_amount,
            "transaction_count": total_count,
            "average_amount": total_amount / total_count if total_count > 0 else 0,
            "by_category": [
                {"category": cat, "count": data["count"], "total": data["total"]}
                for cat, data in sorted(by_category.items(), 
                                       key=lambda x: x[1]["total"], reverse=True)
            ],
            "potential_monthly_savings": total_amount * (30 / days) * 0.5,  # 50% de reducción
        }
    
    @staticmethod
    def get_net_worth(db: Session, user_id: int) -> Dict:
        """Calcular valor neto (activos - pasivos)"""
        # Activos: cuentas positivas + inversiones
        from app.services.transaction_service import TransactionService
        
        asset_accounts = db.query(Account).filter(
            Account.user_id == user_id,
            Account.is_archived == False,
            Account.type.in_(["cash", "debit", "savings"])
        ).all()
        
        total_assets = sum(
            TransactionService.get_account_balance(db, user_id, acc.id)
            for acc in asset_accounts
        )
        
        # Inversiones
        investments = db.query(Investment).filter(
            Investment.user_id == user_id,
            Investment.is_active == True
        ).all()
        
        total_investments = sum(
            inv.quantity * inv.current_price
            for inv in investments
        )
        
        total_assets += total_investments
        
        # Pasivos: deudas de tarjetas de crédito y préstamos
        liability_accounts = db.query(Account).filter(
            Account.user_id == user_id,
            Account.is_archived == False,
            Account.type.in_(["credit", "loan"])
        ).all()
        
        total_liabilities = 0
        for acc in liability_accounts:
            balance = TransactionService.get_account_balance(db, user_id, acc.id)
            # Para cuentas pasivas, el balance negativo es deuda positiva
            total_liabilities += abs(balance) if balance < 0 else balance
        
        net_worth = calculate_net_worth(total_assets, total_liabilities)
        
        return {
            "total_assets": total_assets,
            "cash_and_accounts": total_assets - total_investments,
            "investments": total_investments,
            "total_liabilities": total_liabilities,
            "net_worth": net_worth,
        }
    
    @staticmethod
    def get_monthly_report(db: Session, user_id: int, year: int, month: int) -> Dict:
        """Generar reporte mensual completo"""
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        # Resumen general
        incomes = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.INCOME,
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).scalar() or 0
        
        expenses = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).scalar() or 0
        
        # Gastos por categoría
        by_category = AnalyticsService.get_expense_by_category(
            db, user_id, start_date, end_date
        )
        
        # Estado de presupuestos
        budgets = db.query(Budget).filter(
            Budget.user_id == user_id,
            Budget.is_active == True
        ).all()
        
        from app.services.budget_service import BudgetService
        budget_status = [
            BudgetService.get_budget_with_calculations(db, user_id, b.id)
            for b in budgets
        ]
        
        # Progreso de metas
        goals = db.query(Goal).filter(
            Goal.user_id == user_id,
            Goal.is_completed == False,
            Goal.is_archived == False
        ).all()
        
        from app.services.goal_service import GoalService
        goal_progress = [
            GoalService.get_goal_with_calculations(db, user_id, g.id)
            for g in goals
        ]
        
        return {
            "period": f"{year}-{month:02d}",
            "start_date": start_date,
            "end_date": end_date,
            "summary": {
                "incomes": incomes,
                "expenses": expenses,
                "balance": incomes - expenses,
                "savings_rate": ((incomes - expenses) / incomes * 100) if incomes > 0 else 0
            },
            "expenses_by_category": by_category,
            "budgets": budget_status,
            "goals": goal_progress,
        }

