"""
Modelo de Cuentas
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class AccountType(str, enum.Enum):
    """Tipos de cuenta"""
    CASH = "cash"
    DEBIT = "debit"
    CREDIT = "credit"
    SAVINGS = "savings"
    INVESTMENT = "investment"
    LOAN = "loan"
    RECEIVABLE = "receivable"


class Account(Base):
    """Modelo de cuenta financiera"""
    
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Información básica
    name = Column(String, nullable=False)
    type = Column(Enum(AccountType), nullable=False)
    initial_balance = Column(Float, default=0.0)
    currency = Column(String, default="MXN")
    
    # Personalización
    color = Column(String, default="#2196F3")
    icon = Column(String, default="account_balance_wallet")
    
    # Configuración
    is_default = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    exclude_from_totals = Column(Boolean, default=False)
    
    # Para cuentas por cobrar
    debtor_name = Column(String, nullable=True)
    
    # Orden
    display_order = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    transactions = relationship("Transaction", back_populates="account", foreign_keys="Transaction.account_id")

