"""
Servicio de tarjetas de crédito
"""
from typing import List, Optional, Dict
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException

from app.models.credit_card import CreditCard, CreditCardPeriod, InstallmentPurchase
from app.models.transaction import Transaction, TransactionType
from app.models.account import Account
from app.schemas.credit_card import CreditCardCreate, CreditCardUpdate
from app.utils.calculations import (
    get_next_cutoff_date, get_period_dates,
    calculate_credit_available, calculate_minimum_payment
)


class CreditCardService:
    """Servicio para gestión de tarjetas de crédito"""
    
    @staticmethod
    def create_credit_card(db: Session, user_id: int, card_data: CreditCardCreate) -> CreditCard:
        """Crear tarjeta de crédito"""
        # Validar que la cuenta existe y es del usuario
        account = db.query(Account).filter(
            Account.id == card_data.account_id,
            Account.user_id == user_id
        ).first()
        
        if not account:
            raise HTTPException(status_code=404, detail="Cuenta no encontrada")
        
        # Validar que la cuenta es de tipo crédito
        if account.type.value != "credit":
            raise HTTPException(
                status_code=400,
                detail="La cuenta debe ser de tipo crédito"
            )
        
        # Verificar que no exista ya una tarjeta para esta cuenta
        existing = db.query(CreditCard).filter(
            CreditCard.account_id == card_data.account_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Ya existe una tarjeta configurada para esta cuenta"
            )
        
        # Crear tarjeta
        credit_card = CreditCard(
            account_id=card_data.account_id,
            user_id=user_id,
            card_name=card_data.card_name,
            last_four_digits=card_data.last_four_digits,
            credit_limit=card_data.credit_limit,
            cutoff_day=card_data.cutoff_day,
            payment_due_day=card_data.payment_due_day,
            annual_interest_rate=card_data.annual_interest_rate,
            minimum_payment_percentage=card_data.minimum_payment_percentage,
            color=card_data.color,
            icon=card_data.icon,
        )
        
        db.add(credit_card)
        db.commit()
        db.refresh(credit_card)
        
        return credit_card
    
    @staticmethod
    def get_credit_card_with_calculations(db: Session, user_id: int, 
                                         card_id: int) -> Dict:
        """Obtener tarjeta con todos los cálculos"""
        credit_card = db.query(CreditCard).filter(
            CreditCard.id == card_id,
            CreditCard.user_id == user_id
        ).first()
        
        if not credit_card:
            raise HTTPException(status_code=404, detail="Tarjeta no encontrada")
        
        # Obtener periodos (fechas de corte)
        # Usar get_closed_period_dates para obtener el periodo que ya cerró y está por pagarse
        from app.utils.calculations import get_closed_period_dates
        start_date, cutoff_date = get_closed_period_dates(credit_card.cutoff_day)
        
        # Calcular saldo al corte (transacciones entre fechas del periodo CERRADO)
        # Ejemplo: Si hoy es 26 nov y corte es 15, esto busca gastos del 16 oct al 15 nov
        cutoff_transactions = db.query(Transaction).filter(
            Transaction.account_id == credit_card.account_id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.date >= start_date,
            Transaction.date <= cutoff_date
        ).all()
        
        balance_at_cutoff = sum(t.amount for t in cutoff_transactions)
        
        # Calcular saldo post-corte (después de la fecha de corte)
        post_cutoff_transactions = db.query(Transaction).filter(
            Transaction.account_id == credit_card.account_id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.date > cutoff_date
        ).all()
        
        post_cutoff_balance = sum(t.amount for t in post_cutoff_transactions)
        
        # Calcular deuda total de MSI
        active_installments = db.query(InstallmentPurchase).filter(
            InstallmentPurchase.credit_card_id == credit_card.id,
            InstallmentPurchase.is_active == True,
            InstallmentPurchase.completed == False
        ).all()
        
        total_installment_debt = sum(
            inst.total_amount - (inst.installment_amount * 
            db.query(Transaction).filter(
                Transaction.installment_purchase_id == inst.id
            ).count())
            for inst in active_installments
        )
        
        # Calcular crédito disponible
        available_credit = calculate_credit_available(
            credit_card.credit_limit,
            balance_at_cutoff,
            post_cutoff_balance,
            total_installment_debt
        )
        
        # Calcular pago mínimo
        minimum_payment = calculate_minimum_payment(
            balance_at_cutoff,
            credit_card.minimum_payment_percentage
        )
        
        # Próximas fechas
        next_cutoff = get_next_cutoff_date(credit_card.cutoff_day)
        next_payment = get_next_cutoff_date(credit_card.payment_due_day)
        
        return {
            "credit_card": credit_card,
            "balance_at_cutoff": balance_at_cutoff,
            "post_cutoff_balance": post_cutoff_balance,
            "current_balance": balance_at_cutoff + post_cutoff_balance,
            "available_credit": available_credit,
            "minimum_payment": minimum_payment,
            "total_installment_debt": total_installment_debt,
            "next_cutoff_date": next_cutoff,
            "next_payment_date": next_payment,
            "usage_percentage": (balance_at_cutoff + post_cutoff_balance) / credit_card.credit_limit * 100,
        }
    
    @staticmethod
    def get_installment_purchases(db: Session, user_id: int, 
                                 card_id: int) -> List[Dict]:
        """Obtener compras a MSI con cálculos"""
        credit_card = db.query(CreditCard).filter(
            CreditCard.id == card_id,
            CreditCard.user_id == user_id
        ).first()
        
        if not credit_card:
            raise HTTPException(status_code=404, detail="Tarjeta no encontrada")
        
        installments = db.query(InstallmentPurchase).filter(
            InstallmentPurchase.credit_card_id == card_id,
            InstallmentPurchase.is_active == True
        ).all()
        
        result = []
        for inst in installments:
            # Contar cuotas pagadas
            paid_count = db.query(Transaction).filter(
                Transaction.installment_purchase_id == inst.id
            ).count()
            
            remaining_count = inst.number_of_installments - paid_count
            amount_paid = paid_count * inst.installment_amount
            amount_remaining = remaining_count * inst.installment_amount
            
            result.append({
                "installment_purchase": inst,
                "installments_paid": paid_count,
                "installments_remaining": remaining_count,
                "amount_paid": amount_paid,
                "amount_remaining": amount_remaining,
                "progress_percentage": (paid_count / inst.number_of_installments) * 100
            })
        
        return result
    
    @staticmethod
    def simulate_minimum_payment(db: Session, user_id: int, card_id: int) -> Dict:
        """Simular el costo de pagar solo el mínimo"""
        card_info = CreditCardService.get_credit_card_with_calculations(
            db, user_id, card_id
        )
        
        credit_card = card_info["credit_card"]
        balance = card_info["balance_at_cutoff"]
        
        if balance <= 0:
            return {
                "message": "No hay saldo pendiente",
                "balance": 0,
                "minimum_payment": 0,
                "interest": 0,
                "new_balance": 0,
            }
        
        minimum = calculate_minimum_payment(balance, credit_card.minimum_payment_percentage)
        
        # Calcular interés (aproximado mensual)
        monthly_rate = credit_card.annual_interest_rate / 12 / 100
        interest = (balance - minimum) * monthly_rate
        new_balance = balance - minimum + interest
        
        # Estimar cuántos meses para liquidar
        months_to_payoff = 0
        temp_balance = balance
        while temp_balance > 0 and months_to_payoff < 1200:  # Max 100 años
            min_payment = calculate_minimum_payment(temp_balance, credit_card.minimum_payment_percentage)
            interest_charged = (temp_balance - min_payment) * monthly_rate
            temp_balance = temp_balance - min_payment + interest_charged
            months_to_payoff += 1
            
            if min_payment < 1:  # Evitar loop infinito
                months_to_payoff = -1
                break
        
        return {
            "current_balance": balance,
            "minimum_payment": minimum,
            "interest_if_minimum": interest,
            "new_balance_next_month": new_balance,
            "months_to_payoff": months_to_payoff if months_to_payoff < 1200 else -1,
            "warning": "Pagar solo el mínimo puede resultar en años de deuda y alto costo de intereses"
        }
    
    @staticmethod
    def register_card_payment(db: Session, user_id: int, card_id: int,
                             amount: float, from_account_id: int, 
                             payment_date: datetime) -> Transaction:
        """Registrar pago de tarjeta"""
        # Validar tarjeta
        credit_card = db.query(CreditCard).filter(
            CreditCard.id == card_id,
            CreditCard.user_id == user_id
        ).first()
        
        if not credit_card:
            raise HTTPException(status_code=404, detail="Tarjeta no encontrada")
        
        # Validar cuenta origen
        from_account = db.query(Account).filter(
            Account.id == from_account_id,
            Account.user_id == user_id
        ).first()
        
        if not from_account:
            raise HTTPException(status_code=404, detail="Cuenta origen no encontrada")
        
        # Crear transacción de traspaso
        payment_transaction = Transaction(
            user_id=user_id,
            account_id=from_account_id,
            to_account_id=credit_card.account_id,
            type=TransactionType.TRANSFER,
            amount=amount,
            date=payment_date,
            merchant="Pago de tarjeta",
            notes=f"Pago a {credit_card.card_name}",
        )
        
        db.add(payment_transaction)
        db.commit()
        db.refresh(payment_transaction)
        
        return payment_transaction

    @staticmethod
    def register_simple_payment(db: Session, user_id: int, card_id: int,
                                amount: float) -> Dict:
        """Registrar pago simple de tarjeta (reduce el balance directamente)"""
        # Validar tarjeta
        credit_card = db.query(CreditCard).filter(
            CreditCard.id == card_id,
            CreditCard.user_id == user_id
        ).first()
        
        if not credit_card:
            raise HTTPException(status_code=404, detail="Tarjeta no encontrada")
        
        # Crear transacción de pago (ingreso a la cuenta de la tarjeta)
        payment_date = datetime.now()
        payment_transaction = Transaction(
            user_id=user_id,
            account_id=credit_card.account_id,
            type=TransactionType.INCOME,
            amount=amount,
            date=payment_date,
            merchant="Pago de tarjeta",
            notes=f"Pago a {credit_card.card_name}",
        )
        
        db.add(payment_transaction)
        db.commit()
        db.refresh(payment_transaction)
        
        return {
            "message": "Pago registrado exitosamente",
            "transaction_id": payment_transaction.id,
            "amount": amount,
            "card_name": credit_card.card_name
        }

    @staticmethod
    def delete_credit_card(db: Session, user_id: int, card_id: int):
        """Eliminar tarjeta de crédito"""
        credit_card = db.query(CreditCard).filter(
            CreditCard.id == card_id,
            CreditCard.user_id == user_id
        ).first()
        
        if not credit_card:
            raise HTTPException(status_code=404, detail="Tarjeta no encontrada")
        
        # Verificar si hay transacciones asociadas
        transactions_count = db.query(Transaction).filter(
            Transaction.account_id == credit_card.account_id
        ).count()
        
        if transactions_count > 0:
            # Solo desactivar la tarjeta, no eliminar
            credit_card.is_active = False
            db.commit()
            return {"message": "Tarjeta desactivada (tiene transacciones asociadas)"}
        
        # Si no hay transacciones, eliminar completamente
        db.delete(credit_card)
        db.commit()
        
        return {"message": "Tarjeta eliminada exitosamente"}

