"""
Modelo de Suscripciones
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Subscription(Base):
    """Modelo de suscripción detectada o registrada"""
    
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recurring_transaction_id = Column(Integer, ForeignKey("recurring_transactions.id"), nullable=True)
    
    # Información de la suscripción
    name = Column(String, nullable=False)  # Nombre del servicio
    amount = Column(Float, nullable=False)
    currency = Column(String, default="MXN")
    frequency = Column(String, default="monthly")  # monthly, annual, weekly, biweekly
    billing_day = Column(Integer, nullable=True)  # Día del mes
    
    # Categorización
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    
    # Configuración
    url = Column(String, nullable=True)  # URL del servicio
    notes = Column(String, nullable=True)
    
    # Fechas
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    next_billing_date = Column(DateTime, nullable=True)
    trial_end_date = Column(Date, nullable=True)
    
    # Estado
    is_active = Column(Boolean, default=True)
    is_detected = Column(Boolean, default=False)  # True si fue detectada automáticamente
    is_investment = Column(Boolean, default=False)  # True si es una cuota de inversión
    investment_id = Column(Integer, nullable=True)  # ID de la inversión relacionada
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    category = relationship("Category")
    account = relationship("Account")
    recurring_transaction = relationship("RecurringTransaction")

