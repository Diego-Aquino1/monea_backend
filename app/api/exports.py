"""
Endpoints de exportación de datos
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, date
import csv
import io
import json

from app.database import get_db
from app.models.user import User
from app.models.transaction import Transaction
from app.models.account import Account
from app.models.category import Category
from app.utils.security import get_current_active_user

router = APIRouter()


@router.get("/transactions/csv")
def export_transactions_csv(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    account_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Exportar transacciones a CSV"""
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)
    
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    
    transactions = query.order_by(Transaction.date.desc()).all()
    
    # Obtener cuentas y categorías para los nombres
    accounts = {a.id: a.name for a in db.query(Account).filter(
        Account.user_id == current_user.id
    ).all()}
    categories = {c.id: c.name for c in db.query(Category).filter(
        Category.user_id == current_user.id
    ).all()}
    
    # Crear CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        'Fecha', 'Tipo', 'Monto', 'Moneda', 'Cuenta', 'Categoría',
        'Comercio', 'Notas', 'Etiquetas', 'Reembolsable', 'Diferido'
    ])
    
    # Datos
    for tx in transactions:
        writer.writerow([
            tx.date.strftime('%Y-%m-%d %H:%M'),
            tx.type.value,
            tx.amount,
            tx.currency,
            accounts.get(tx.account_id, 'N/A'),
            categories.get(tx.category_id, 'N/A'),
            tx.merchant or '',
            tx.notes or '',
            tx.tags or '',
            'Sí' if tx.is_reimbursable else 'No',
            'Sí' if tx.is_installment else 'No'
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=transacciones_{date.today().isoformat()}.csv"
        }
    )


@router.get("/transactions/json")
def export_transactions_json(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Exportar transacciones a JSON"""
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)
    
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    
    transactions = query.order_by(Transaction.date.desc()).all()
    
    data = []
    for tx in transactions:
        data.append({
            "id": tx.id,
            "date": tx.date.isoformat(),
            "type": tx.type.value,
            "amount": tx.amount,
            "currency": tx.currency,
            "account_id": tx.account_id,
            "category_id": tx.category_id,
            "merchant": tx.merchant,
            "notes": tx.notes,
            "tags": tx.tags,
            "is_reimbursable": tx.is_reimbursable,
            "is_installment": tx.is_installment
        })
    
    output = io.StringIO()
    json.dump(data, output, ensure_ascii=False, indent=2)
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=transacciones_{date.today().isoformat()}.json"
        }
    )


@router.get("/all-data")
def export_all_data(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Exportar todos los datos del usuario (backup completo)"""
    from app.models.budget import Budget
    from app.models.goal import Goal
    from app.models.credit_card import CreditCard
    from app.models.subscription import Subscription
    
    # Recopilar todos los datos
    data = {
        "export_date": datetime.now().isoformat(),
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "currency": current_user.default_currency
        },
        "accounts": [],
        "categories": [],
        "transactions": [],
        "budgets": [],
        "goals": [],
        "credit_cards": [],
        "subscriptions": []
    }
    
    # Cuentas
    accounts = db.query(Account).filter(Account.user_id == current_user.id).all()
    for acc in accounts:
        data["accounts"].append({
            "id": acc.id,
            "name": acc.name,
            "type": acc.type,
            "currency": acc.currency,
            "initial_balance": acc.initial_balance,
            "is_archived": acc.is_archived
        })
    
    # Categorías
    categories = db.query(Category).filter(Category.user_id == current_user.id).all()
    for cat in categories:
        data["categories"].append({
            "id": cat.id,
            "name": cat.name,
            "icon": cat.icon,
            "color": cat.color,
            "parent_id": cat.parent_id,
            "is_income": cat.is_income
        })
    
    # Transacciones
    transactions = db.query(Transaction).filter(Transaction.user_id == current_user.id).all()
    for tx in transactions:
        data["transactions"].append({
            "id": tx.id,
            "date": tx.date.isoformat(),
            "type": tx.type.value,
            "amount": tx.amount,
            "currency": tx.currency,
            "account_id": tx.account_id,
            "category_id": tx.category_id,
            "merchant": tx.merchant,
            "notes": tx.notes,
            "tags": tx.tags
        })
    
    # Presupuestos
    budgets = db.query(Budget).filter(Budget.user_id == current_user.id).all()
    for budget in budgets:
        data["budgets"].append({
            "id": budget.id,
            "name": budget.name,
            "amount": budget.amount,
            "period": budget.period,
            "category_id": budget.category_id,
            "rollover": budget.rollover_enabled
        })
    
    # Metas
    goals = db.query(Goal).filter(Goal.user_id == current_user.id).all()
    for goal in goals:
        data["goals"].append({
            "id": goal.id,
            "name": goal.name,
            "target_amount": goal.target_amount,
            "current_amount": goal.current_amount,
            "target_date": goal.target_date.isoformat() if goal.target_date else None
        })
    
    # Tarjetas
    cards = db.query(CreditCard).filter(CreditCard.user_id == current_user.id).all()
    for card in cards:
        data["credit_cards"].append({
            "id": card.id,
            "name": card.card_name,
            "credit_limit": card.credit_limit,
            "cutoff_day": card.cutoff_day,
            "payment_due_day": card.payment_due_day
        })
    
    # Suscripciones
    subs = db.query(Subscription).filter(Subscription.user_id == current_user.id).all()
    for sub in subs:
        data["subscriptions"].append({
            "id": sub.id,
            "name": sub.name,
            "amount": sub.amount,
            "frequency": sub.frequency,
            "is_active": sub.is_active
        })
    
    output = io.StringIO()
    json.dump(data, output, ensure_ascii=False, indent=2)
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=nexus_backup_{date.today().isoformat()}.json"
        }
    )

