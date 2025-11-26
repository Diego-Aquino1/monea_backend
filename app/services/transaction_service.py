"""
Servicio de transacciones
"""
from typing import List, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status

from app.models.transaction import Transaction, TransactionSplit, TransactionType
from app.models.account import Account
from app.models.credit_card import CreditCard, InstallmentPurchase
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app.utils.calculations import get_period_dates
from dateutil.relativedelta import relativedelta


class TransactionService:
    """Servicio para gestión de transacciones"""
    
    @staticmethod
    def create_transaction(db: Session, user_id: int, transaction_data: TransactionCreate) -> Transaction:
        """
        Crear transacción con lógica completa
        - Maneja splits
        - Maneja MSI
        - Valida cuentas
        """
        # Validar cuenta
        # Primero verificar que la cuenta existe
        account = db.query(Account).filter(
            Account.id == transaction_data.account_id
        ).first()
        
        if not account:
            raise HTTPException(
                status_code=404, 
                detail=f"Cuenta con ID {transaction_data.account_id} no encontrada. Por favor, recarga tus cuentas."
            )
        
        # Verificar que la cuenta pertenece al usuario
        if account.user_id != user_id:
            raise HTTPException(
                status_code=403, 
                detail=f"La cuenta con ID {transaction_data.account_id} no pertenece a tu usuario."
            )
        
        # Verificar que la cuenta no esté archivada
        if account.is_archived:
            raise HTTPException(
                status_code=400,
                detail=f"La cuenta con ID {transaction_data.account_id} está archivada. Actívala primero para poder crear transacciones."
            )
        
        # Si es transfer, validar cuenta destino
        if transaction_data.type == TransactionType.TRANSFER:
            if not transaction_data.to_account_id:
                raise HTTPException(status_code=400, detail="Cuenta destino requerida para transferencias")
            
            to_account = db.query(Account).filter(
                Account.id == transaction_data.to_account_id,
                Account.user_id == user_id
            ).first()
            
            if not to_account:
                raise HTTPException(status_code=404, detail="Cuenta destino no encontrada")
            
            if transaction_data.account_id == transaction_data.to_account_id:
                raise HTTPException(status_code=400, detail="Las cuentas no pueden ser iguales")
        
        # Si hay splits, validar suma
        if transaction_data.splits:
            total_splits = sum(split.amount for split in transaction_data.splits)
            if abs(total_splits - transaction_data.amount) > 0.01:
                raise HTTPException(
                    status_code=400,
                    detail=f"La suma de splits ({total_splits}) no coincide con el monto total ({transaction_data.amount})"
                )
        
        # Crear transacción principal
        transaction = Transaction(
            user_id=user_id,
            account_id=transaction_data.account_id,
            category_id=transaction_data.category_id,
            type=transaction_data.type,
            amount=transaction_data.amount,
            currency=transaction_data.currency,
            date=transaction_data.date,
            time=transaction_data.time,
            merchant=transaction_data.merchant,
            notes=transaction_data.notes,
            tags=transaction_data.tags,
            to_account_id=transaction_data.to_account_id,
            is_reimbursable=transaction_data.is_reimbursable,
            location_lat=transaction_data.location_lat,
            location_lng=transaction_data.location_lng,
            location_name=transaction_data.location_name,
            is_split=bool(transaction_data.splits),
        )
        
        db.add(transaction)
        db.flush()  # Para obtener el ID
        
        # Si hay splits, crearlos
        if transaction_data.splits:
            for split_data in transaction_data.splits:
                split = TransactionSplit(
                    parent_transaction_id=transaction.id,
                    category_id=split_data.category_id,
                    amount=split_data.amount,
                    notes=split_data.notes
                )
                db.add(split)
        
        # Si es compra a MSI, crear cuotas
        if transaction_data.installment_months:
            TransactionService._create_installment_purchase(
                db, user_id, transaction, transaction_data.installment_months
            )
        
        db.commit()
        db.refresh(transaction)
        
        return transaction
    
    @staticmethod
    def _create_installment_purchase(db: Session, user_id: int, transaction: Transaction, 
                                     months: int):
        """Crear compra a MSI y sus cuotas"""
        # Verificar que la cuenta sea una tarjeta de crédito
        credit_card = db.query(CreditCard).filter(
            CreditCard.account_id == transaction.account_id
        ).first()
        
        if not credit_card:
            raise HTTPException(
                status_code=400,
                detail="Solo se pueden diferir compras en tarjetas de crédito"
            )
        
        # Calcular monto de cuota
        installment_amount = transaction.amount / months
        
        # Crear registro de compra a MSI
        installment_purchase = InstallmentPurchase(
            credit_card_id=credit_card.id,
            user_id=user_id,
            category_id=transaction.category_id,
            description=transaction.merchant or "Compra a MSI",
            merchant=transaction.merchant,
            total_amount=transaction.amount,
            number_of_installments=months,
            installment_amount=installment_amount,
            purchase_date=transaction.date.date() if isinstance(transaction.date, datetime) else transaction.date,
            first_installment_date=transaction.date.date() if isinstance(transaction.date, datetime) else transaction.date,
        )
        
        db.add(installment_purchase)
        db.flush()
        
        # Vincular transacción actual como primera cuota
        transaction.is_installment = True
        transaction.installment_purchase_id = installment_purchase.id
        transaction.installment_number = 1
        transaction.amount = installment_amount
        
        # Crear transacciones futuras para las demás cuotas
        cutoff_day = credit_card.cutoff_day
        current_date = transaction.date.date() if isinstance(transaction.date, datetime) else transaction.date
        
        for i in range(2, months + 1):
            # Calcular fecha de próxima cuota (próximo corte)
            next_date = current_date + relativedelta(months=i-1)
            
            future_transaction = Transaction(
                user_id=user_id,
                account_id=transaction.account_id,
                category_id=transaction.category_id,
                type=TransactionType.EXPENSE,
                amount=installment_amount,
                currency=transaction.currency,
                date=next_date,
                merchant=transaction.merchant,
                notes=f"Cuota {i}/{months} - {transaction.merchant or 'MSI'}",
                is_installment=True,
                installment_purchase_id=installment_purchase.id,
                installment_number=i,
            )
            db.add(future_transaction)
    
    @staticmethod
    def get_transactions(db: Session, user_id: int, skip: int = 0, limit: int = 100,
                        account_id: Optional[int] = None,
                        category_id: Optional[int] = None,
                        type: Optional[TransactionType] = None,
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None) -> List[Transaction]:
        """Obtener transacciones con filtros"""
        from sqlalchemy.orm import joinedload
        
        query = db.query(Transaction).filter(Transaction.user_id == user_id)
        
        # Eager load para obtener account_name y category_name
        query = query.options(
            joinedload(Transaction.account),
            joinedload(Transaction.category)
        )
        
        if account_id:
            query = query.filter(Transaction.account_id == account_id)
        
        if category_id:
            query = query.filter(Transaction.category_id == category_id)
        
        if type:
            query = query.filter(Transaction.type == type)
        
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        
        query = query.order_by(Transaction.date.desc())
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def update_transaction(db: Session, user_id: int, transaction_id: int,
                          update_data: TransactionUpdate) -> Transaction:
        """Actualizar transacción"""
        transaction = db.query(Transaction).filter(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id
        ).first()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transacción no encontrada")
        
        # Actualizar campos
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(transaction, field, value)
        
        db.commit()
        db.refresh(transaction)
        
        return transaction
    
    @staticmethod
    def delete_transaction(db: Session, user_id: int, transaction_id: int):
        """Eliminar transacción"""
        transaction = db.query(Transaction).filter(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id
        ).first()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transacción no encontrada")
        
        # Si es parte de un MSI, manejar especialmente
        if transaction.is_installment and transaction.installment_number == 1:
            # Si es la primera cuota, eliminar toda la compra a MSI
            installment_purchase = db.query(InstallmentPurchase).filter(
                InstallmentPurchase.id == transaction.installment_purchase_id
            ).first()
            
            if installment_purchase:
                # Eliminar todas las cuotas
                db.query(Transaction).filter(
                    Transaction.installment_purchase_id == installment_purchase.id
                ).delete()
                
                # Eliminar registro de MSI
                db.delete(installment_purchase)
        else:
            db.delete(transaction)
        
        db.commit()
    
    @staticmethod
    def get_account_balance(db: Session, user_id: int, account_id: int) -> float:
        """Calcular saldo actual de una cuenta"""
        account = db.query(Account).filter(
            Account.id == account_id,
            Account.user_id == user_id
        ).first()
        
        if not account:
            raise HTTPException(status_code=404, detail="Cuenta no encontrada")
        
        # Sumar ingresos
        incomes = db.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.type == TransactionType.INCOME
        ).all()
        total_incomes = sum(t.amount for t in incomes)
        
        # Sumar gastos
        expenses = db.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.type == TransactionType.EXPENSE
        ).all()
        total_expenses = sum(t.amount for t in expenses)
        
        # Traspasos entrantes
        transfers_in = db.query(Transaction).filter(
            Transaction.to_account_id == account_id,
            Transaction.type == TransactionType.TRANSFER
        ).all()
        total_transfers_in = sum(t.amount for t in transfers_in)
        
        # Traspasos salientes
        transfers_out = db.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.type == TransactionType.TRANSFER
        ).all()
        total_transfers_out = sum(t.amount for t in transfers_out)
        
        # Calcular saldo
        balance = (
            account.initial_balance +
            total_incomes -
            total_expenses +
            total_transfers_in -
            total_transfers_out
        )
        
        return balance

