"""
Servicio de transacciones recurrentes
"""
from typing import List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.transaction import Transaction, RecurringTransaction, TransactionType, RecurrenceFrequency
from app.models.account import Account
from dateutil.relativedelta import relativedelta


class RecurringTransactionService:
    """Servicio para gestión de transacciones recurrentes"""
    
    @staticmethod
    def create_recurring(db: Session, user_id: int, data: dict) -> RecurringTransaction:
        """Crear transacción recurrente"""
        # Validar cuenta
        account = db.query(Account).filter(
            Account.id == data['account_id'],
            Account.user_id == user_id
        ).first()
        
        if not account:
            raise HTTPException(status_code=404, detail="Cuenta no encontrada")
        
        recurring = RecurringTransaction(
            user_id=user_id,
            account_id=data['account_id'],
            category_id=data.get('category_id'),
            name=data['name'],
            type=data['type'],
            amount=data['amount'],
            is_variable_amount=data.get('is_variable_amount', False),
            frequency=data['frequency'],
            custom_frequency_days=data.get('custom_frequency_days'),
            day_of_month=data.get('day_of_month'),
            day_of_week=data.get('day_of_week'),
            start_date=data['start_date'],
            end_date=data.get('end_date'),
            auto_create=data.get('auto_create', True),
            notify_before_days=data.get('notify_before_days', 2),
            merchant=data.get('merchant'),
            notes=data.get('notes'),
        )
        
        db.add(recurring)
        db.commit()
        db.refresh(recurring)
        
        # Si auto_create y la fecha de inicio es hoy o pasada, crear primera transacción
        if recurring.auto_create and recurring.start_date.date() <= date.today():
            RecurringTransactionService._create_transaction_from_recurring(db, recurring)
        
        return recurring
    
    @staticmethod
    def get_recurring_transactions(db: Session, user_id: int, 
                                   active_only: bool = True) -> List[RecurringTransaction]:
        """Obtener transacciones recurrentes"""
        query = db.query(RecurringTransaction).filter(
            RecurringTransaction.user_id == user_id
        )
        
        if active_only:
            query = query.filter(RecurringTransaction.is_active == True)
        
        return query.order_by(RecurringTransaction.name).all()
    
    @staticmethod
    def update_recurring(db: Session, user_id: int, recurring_id: int, 
                        data: dict) -> RecurringTransaction:
        """Actualizar transacción recurrente"""
        recurring = db.query(RecurringTransaction).filter(
            RecurringTransaction.id == recurring_id,
            RecurringTransaction.user_id == user_id
        ).first()
        
        if not recurring:
            raise HTTPException(status_code=404, detail="Transacción recurrente no encontrada")
        
        for key, value in data.items():
            if hasattr(recurring, key) and value is not None:
                setattr(recurring, key, value)
        
        db.commit()
        db.refresh(recurring)
        
        return recurring
    
    @staticmethod
    def delete_recurring(db: Session, user_id: int, recurring_id: int, 
                        delete_future: bool = False):
        """Eliminar o desactivar transacción recurrente"""
        recurring = db.query(RecurringTransaction).filter(
            RecurringTransaction.id == recurring_id,
            RecurringTransaction.user_id == user_id
        ).first()
        
        if not recurring:
            raise HTTPException(status_code=404, detail="Transacción recurrente no encontrada")
        
        if delete_future:
            # Eliminar transacciones futuras no realizadas
            db.query(Transaction).filter(
                Transaction.recurring_transaction_id == recurring_id,
                Transaction.date > datetime.now()
            ).delete()
        
        # Desactivar en lugar de eliminar
        recurring.is_active = False
        db.commit()
    
    @staticmethod
    def process_pending_recurring(db: Session):
        """Procesar transacciones recurrentes pendientes (ejecutar en cron/job)"""
        today = date.today()
        
        # Obtener todas las recurrentes activas con auto_create
        recurring_list = db.query(RecurringTransaction).filter(
            RecurringTransaction.is_active == True,
            RecurringTransaction.auto_create == True
        ).all()
        
        created_count = 0
        
        for recurring in recurring_list:
            # Verificar si ya pasó la fecha de fin
            if recurring.end_date and recurring.end_date.date() < today:
                recurring.is_active = False
                continue
            
            # Calcular próxima fecha de ejecución
            next_date = RecurringTransactionService._calculate_next_date(recurring)
            
            if next_date and next_date <= today:
                # Verificar que no se haya creado ya
                existing = db.query(Transaction).filter(
                    Transaction.recurring_transaction_id == recurring.id,
                    Transaction.date >= datetime.combine(next_date, datetime.min.time()),
                    Transaction.date < datetime.combine(next_date + timedelta(days=1), datetime.min.time())
                ).first()
                
                if not existing:
                    RecurringTransactionService._create_transaction_from_recurring(
                        db, recurring, next_date
                    )
                    created_count += 1
        
        db.commit()
        return created_count
    
    @staticmethod
    def _calculate_next_date(recurring: RecurringTransaction) -> Optional[date]:
        """Calcular próxima fecha de ejecución"""
        last_date = recurring.last_created_date.date() if recurring.last_created_date else None
        start = recurring.start_date.date()
        today = date.today()
        
        if last_date is None:
            return start if start <= today else None
        
        # Calcular siguiente fecha según frecuencia
        if recurring.frequency == RecurrenceFrequency.DAILY:
            next_date = last_date + timedelta(days=1)
        
        elif recurring.frequency == RecurrenceFrequency.WEEKLY:
            next_date = last_date + timedelta(weeks=1)
        
        elif recurring.frequency == RecurrenceFrequency.BIWEEKLY:
            next_date = last_date + timedelta(weeks=2)
        
        elif recurring.frequency == RecurrenceFrequency.MONTHLY:
            next_date = last_date + relativedelta(months=1)
            if recurring.day_of_month:
                try:
                    next_date = date(next_date.year, next_date.month, recurring.day_of_month)
                except ValueError:
                    # Si el día no existe (ej: 31 de febrero), usar último día del mes
                    next_date = date(next_date.year, next_date.month + 1, 1) - timedelta(days=1)
        
        elif recurring.frequency == RecurrenceFrequency.BIMONTHLY:
            next_date = last_date + relativedelta(months=2)
        
        elif recurring.frequency == RecurrenceFrequency.QUARTERLY:
            next_date = last_date + relativedelta(months=3)
        
        elif recurring.frequency == RecurrenceFrequency.SEMIANNUAL:
            next_date = last_date + relativedelta(months=6)
        
        elif recurring.frequency == RecurrenceFrequency.ANNUAL:
            next_date = last_date + relativedelta(years=1)
        
        elif recurring.frequency == RecurrenceFrequency.CUSTOM:
            days = recurring.custom_frequency_days or 30
            next_date = last_date + timedelta(days=days)
        
        else:
            return None
        
        return next_date if next_date <= today else None
    
    @staticmethod
    def _create_transaction_from_recurring(db: Session, recurring: RecurringTransaction,
                                          transaction_date: date = None):
        """Crear transacción a partir de recurrente"""
        if transaction_date is None:
            transaction_date = date.today()
        
        transaction = Transaction(
            user_id=recurring.user_id,
            account_id=recurring.account_id,
            category_id=recurring.category_id,
            type=recurring.type,
            amount=recurring.amount,
            date=datetime.combine(transaction_date, datetime.min.time()),
            merchant=recurring.merchant,
            notes=f"[Auto] {recurring.notes or recurring.name}",
            recurring_transaction_id=recurring.id,
        )
        
        db.add(transaction)
        recurring.last_created_date = datetime.now()
        db.flush()
        
        return transaction
    
    @staticmethod
    def get_upcoming_recurring(db: Session, user_id: int, days: int = 7) -> List[dict]:
        """Obtener transacciones recurrentes próximas a ejecutarse"""
        today = date.today()
        end_date = today + timedelta(days=days)
        
        recurring_list = db.query(RecurringTransaction).filter(
            RecurringTransaction.user_id == user_id,
            RecurringTransaction.is_active == True
        ).all()
        
        upcoming = []
        
        for recurring in recurring_list:
            next_date = RecurringTransactionService._calculate_next_date(recurring)
            
            if next_date is None:
                # Si no hay última fecha, usar start_date
                if recurring.start_date.date() <= end_date:
                    next_date = recurring.start_date.date()
            
            if next_date and today <= next_date <= end_date:
                upcoming.append({
                    "recurring": recurring,
                    "next_date": next_date,
                    "days_until": (next_date - today).days
                })
        
        return sorted(upcoming, key=lambda x: x["next_date"])

