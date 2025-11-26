"""
Modelos de Tarjetas de Crédito
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class CreditCard(Base):
    """Modelo de tarjeta de crédito"""
    
    __tablename__ = "credit_cards"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Información de la tarjeta
    card_name = Column(String, nullable=False)
    last_four_digits = Column(String(4), nullable=True)
    
    # Configuración financiera
    credit_limit = Column(Float, nullable=False)
    cutoff_day = Column(Integer, nullable=False)  # Día de corte (1-28)
    payment_due_day = Column(Integer, nullable=False)  # Día límite de pago
    
    # Tasas e intereses
    annual_interest_rate = Column(Float, default=0.0)  # Tasa anual (ej: 48.0 para 48%)
    minimum_payment_percentage = Column(Float, default=5.0)  # Porcentaje de pago mínimo
    
    # Personalización
    color = Column(String, default="#FF5722")
    icon = Column(String, default="credit_card")
    
    # Configuración de alertas
    alert_days_before_cutoff = Column(Integer, default=3)
    alert_days_before_payment = Column(Integer, default=5)
    alert_when_usage_exceeds = Column(Float, default=80.0)  # Porcentaje de uso
    
    # Estado
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    account = relationship("Account")
    periods = relationship("CreditCardPeriod", back_populates="credit_card")
    installment_purchases = relationship("InstallmentPurchase", back_populates="credit_card")


class CreditCardPeriod(Base):
    """Periodo de facturación de tarjeta de crédito"""
    
    __tablename__ = "credit_card_periods"
    
    id = Column(Integer, primary_key=True, index=True)
    credit_card_id = Column(Integer, ForeignKey("credit_cards.id"), nullable=False)
    
    # Fechas del periodo
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)  # Fecha de corte
    payment_due_date = Column(Date, nullable=False)
    
    # Saldos calculados
    balance_at_cutoff = Column(Float, default=0.0)  # Saldo al corte
    minimum_payment = Column(Float, default=0.0)
    
    # Estado de pago
    is_paid = Column(Boolean, default=False)
    payment_amount = Column(Float, nullable=True)
    payment_date = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    credit_card = relationship("CreditCard", back_populates="periods")


class InstallmentPurchase(Base):
    """Compra a meses sin intereses (MSI)"""
    
    __tablename__ = "installment_purchases"
    
    id = Column(Integer, primary_key=True, index=True)
    credit_card_id = Column(Integer, ForeignKey("credit_cards.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    # Información de la compra
    description = Column(String, nullable=False)
    merchant = Column(String, nullable=True)
    total_amount = Column(Float, nullable=False)
    
    # Configuración de cuotas
    number_of_installments = Column(Integer, nullable=False)
    installment_amount = Column(Float, nullable=False)
    
    # Fechas
    purchase_date = Column(Date, nullable=False)
    first_installment_date = Column(Date, nullable=False)
    
    # Estado
    is_active = Column(Boolean, default=True)
    completed = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    credit_card = relationship("CreditCard", back_populates="installment_purchases")
    category = relationship("Category")
    transactions = relationship("Transaction", back_populates="installment_purchase")

