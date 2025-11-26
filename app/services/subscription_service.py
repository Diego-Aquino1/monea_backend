"""
Servicio de suscripciones y detección
"""
from typing import List, Dict
from datetime import datetime, date, timedelta
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.subscription import Subscription
from app.models.transaction import Transaction, TransactionType


class SubscriptionService:
    """Servicio para detección y gestión de suscripciones"""
    
    @staticmethod
    def get_subscriptions(db: Session, user_id: int, 
                         active_only: bool = True) -> List[Subscription]:
        """Obtener suscripciones del usuario"""
        query = db.query(Subscription).filter(Subscription.user_id == user_id)
        
        if active_only:
            query = query.filter(Subscription.is_active == True)
        
        return query.order_by(Subscription.name).all()
    
    @staticmethod
    def create_subscription(db: Session, user_id: int, data: dict) -> Subscription:
        """Crear suscripción manualmente"""
        subscription = Subscription(
            user_id=user_id,
            name=data['name'],
            amount=data['amount'],
            currency=data.get('currency', 'PEN'),
            frequency=data.get('frequency', 'monthly'),
            billing_day=data.get('billing_day'),
            category_id=data.get('category_id'),
            account_id=data.get('account_id'),
            start_date=data.get('start_date', datetime.now()),
            next_billing_date=data.get('next_billing_date'),
            notes=data.get('notes'),
            url=data.get('url'),
            is_active=True,
            is_investment=data.get('is_investment', False),
            investment_id=data.get('investment_id')
        )
        
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        
        return subscription
    
    @staticmethod
    def update_subscription(db: Session, user_id: int, 
                           subscription_id: int, data: dict) -> Subscription:
        """Actualizar suscripción"""
        subscription = db.query(Subscription).filter(
            Subscription.id == subscription_id,
            Subscription.user_id == user_id
        ).first()
        
        if not subscription:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Suscripción no encontrada")
        
        for key, value in data.items():
            if hasattr(subscription, key) and value is not None:
                setattr(subscription, key, value)
        
        db.commit()
        db.refresh(subscription)
        
        return subscription
    
    @staticmethod
    def cancel_subscription(db: Session, user_id: int, 
                           subscription_id: int, end_date: date = None):
        """Cancelar suscripción"""
        subscription = db.query(Subscription).filter(
            Subscription.id == subscription_id,
            Subscription.user_id == user_id
        ).first()
        
        if subscription:
            subscription.is_active = False
            subscription.end_date = end_date or datetime.now()
            db.commit()
    
    @staticmethod
    def detect_subscriptions(db: Session, user_id: int, 
                            months: int = 3) -> List[Dict]:
        """
        Detectar posibles suscripciones basándose en patrones de gasto.
        
        Busca transacciones que:
        - Tienen el mismo comercio/descripción
        - Ocurren regularmente (mensual, anual, etc.)
        - Tienen montos similares
        """
        start_date = datetime.now() - timedelta(days=months * 30)
        
        # Obtener transacciones de los últimos N meses
        transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.date >= start_date
        ).all()
        
        # Agrupar por comercio y monto
        patterns = defaultdict(list)
        
        for tx in transactions:
            # Usar comercio o notas como identificador
            key = (tx.merchant or tx.notes or "desconocido", round(tx.amount, 0))
            patterns[key].append(tx)
        
        detected = []
        
        for (merchant, amount), txs in patterns.items():
            if len(txs) >= 2:  # Al menos 2 ocurrencias
                # Calcular intervalo promedio entre transacciones
                dates = sorted([tx.date for tx in txs])
                intervals = [
                    (dates[i+1] - dates[i]).days 
                    for i in range(len(dates)-1)
                ]
                avg_interval = sum(intervals) / len(intervals) if intervals else 0
                
                # Determinar frecuencia
                frequency = None
                confidence = 0
                
                if 25 <= avg_interval <= 35:
                    frequency = "monthly"
                    confidence = 0.8
                elif 350 <= avg_interval <= 380:
                    frequency = "annual"
                    confidence = 0.7
                elif 12 <= avg_interval <= 16:
                    frequency = "biweekly"
                    confidence = 0.6
                elif 5 <= avg_interval <= 9:
                    frequency = "weekly"
                    confidence = 0.6
                
                if frequency:
                    # Verificar si ya existe como suscripción
                    existing = db.query(Subscription).filter(
                        Subscription.user_id == user_id,
                        Subscription.name.ilike(f"%{merchant}%")
                    ).first()
                    
                    if not existing:
                        # Calcular próxima fecha probable
                        last_date = dates[-1].date()
                        next_date = last_date + timedelta(days=int(avg_interval))
                        
                        detected.append({
                            "merchant": merchant,
                            "amount": amount,
                            "frequency": frequency,
                            "occurrences": len(txs),
                            "avg_interval_days": round(avg_interval, 1),
                            "confidence": confidence,
                            "last_charge": last_date.isoformat(),
                            "next_charge_estimate": next_date.isoformat(),
                            "sample_transactions": [tx.id for tx in txs[:3]]
                        })
        
        # Ordenar por confianza
        detected.sort(key=lambda x: x["confidence"], reverse=True)
        
        return detected
    
    @staticmethod
    def confirm_detected_subscription(db: Session, user_id: int, 
                                     detection: dict) -> Subscription:
        """Confirmar una suscripción detectada"""
        data = {
            "name": detection["merchant"],
            "amount": detection["amount"],
            "frequency": detection["frequency"],
            "billing_day": None,  # Se calculará de la próxima fecha
        }
        
        return SubscriptionService.create_subscription(db, user_id, data)
    
    @staticmethod
    def get_monthly_subscription_total(db: Session, user_id: int) -> Dict:
        """Obtener total mensual en suscripciones"""
        subscriptions = SubscriptionService.get_subscriptions(
            db, user_id, active_only=True
        )
        
        monthly_total = 0
        annual_total = 0
        
        for sub in subscriptions:
            if sub.frequency == "monthly":
                monthly_total += sub.amount
            elif sub.frequency == "annual":
                monthly_total += sub.amount / 12
            elif sub.frequency == "biweekly":
                monthly_total += sub.amount * 2
            elif sub.frequency == "weekly":
                monthly_total += sub.amount * 4.33
        
        annual_total = monthly_total * 12
        
        return {
            "monthly_total": round(monthly_total, 2),
            "annual_total": round(annual_total, 2),
            "active_count": len(subscriptions),
            "subscriptions": [
                {
                    "id": s.id,
                    "name": s.name,
                    "amount": s.amount,
                    "frequency": s.frequency
                }
                for s in subscriptions
            ]
        }
    
    @staticmethod
    def get_upcoming_renewals(db: Session, user_id: int, days: int = 7) -> List[Dict]:
        """Obtener renovaciones próximas"""
        today = date.today()
        end_date = today + timedelta(days=days)
        
        subscriptions = db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.is_active == True,
            Subscription.next_billing_date != None,
            Subscription.next_billing_date >= today,
            Subscription.next_billing_date <= end_date
        ).order_by(Subscription.next_billing_date).all()
        
        return [
            {
                "id": s.id,
                "name": s.name,
                "amount": s.amount,
                "next_billing_date": s.next_billing_date.isoformat() if s.next_billing_date else None,
                "days_until": (s.next_billing_date - today).days if s.next_billing_date else None
            }
            for s in subscriptions
        ]

