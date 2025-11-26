"""
Modelos de Transacciones
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class TransactionType(str, enum.Enum):
    """Tipo de transacción"""
    EXPENSE = "expense"
    INCOME = "income"
    TRANSFER = "transfer"


class RecurrenceFrequency(str, enum.Enum):
    """Frecuencia de recurrencia"""
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    BIMONTHLY = "bimonthly"
    QUARTERLY = "quarterly"
    SEMIANNUAL = "semiannual"
    ANNUAL = "annual"
    CUSTOM = "custom"


class Transaction(Base):
    """Modelo de transacción financiera"""
    
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    # Información básica
    type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="MXN")
    
    # Fecha y hora
    date = Column(DateTime, nullable=False)
    time = Column(String, nullable=True)
    
    # Descripción
    merchant = Column(String, nullable=True)  # Comercio/Pagador
    notes = Column(Text, nullable=True)
    tags = Column(String, nullable=True)  # JSON string con tags
    
    # Ubicación
    location_lat = Column(Float, nullable=True)
    location_lng = Column(Float, nullable=True)
    location_name = Column(String, nullable=True)
    
    # Archivos adjuntos
    receipt_path = Column(String, nullable=True)
    
    # Transferencias
    to_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    
    # Características especiales
    is_reimbursable = Column(Boolean, default=False)
    reimbursed = Column(Boolean, default=False)
    reimbursement_date = Column(DateTime, nullable=True)
    
    # Diferido en cuotas
    is_installment = Column(Boolean, default=False)
    installment_purchase_id = Column(Integer, ForeignKey("installment_purchases.id"), nullable=True)
    installment_number = Column(Integer, nullable=True)  # Número de cuota (1, 2, 3...)
    
    # División
    is_split = Column(Boolean, default=False)
    parent_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    
    # Recurrencia
    recurring_transaction_id = Column(Integer, ForeignKey("recurring_transactions.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    account = relationship("Account", back_populates="transactions", foreign_keys=[account_id])
    to_account = relationship("Account", foreign_keys=[to_account_id])
    category = relationship("Category", back_populates="transactions")
    splits = relationship("TransactionSplit", back_populates="parent_transaction")
    parent_transaction = relationship("Transaction", remote_side=[id], backref="child_transactions")
    recurring_transaction = relationship("RecurringTransaction", back_populates="transactions")
    installment_purchase = relationship("InstallmentPurchase", back_populates="transactions")
    
    # Propiedades calculadas para serialización
    @property
    def account_name(self) -> str:
        """Nombre de la cuenta"""
        return self.account.name if self.account else None
    
    @property
    def category_name(self) -> str:
        """Nombre de la categoría"""
        return self.category.name if self.category else None


class TransactionSplit(Base):
    """División de transacción en múltiples categorías"""
    
    __tablename__ = "transaction_splits"
    
    id = Column(Integer, primary_key=True, index=True)
    parent_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    
    amount = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    parent_transaction = relationship("Transaction", back_populates="splits")
    category = relationship("Category")


class RecurringTransaction(Base):
    """Transacción recurrente/programada"""
    
    __tablename__ = "recurring_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    # Información básica
    name = Column(String, nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Float, nullable=False)
    is_variable_amount = Column(Boolean, default=False)  # Si el monto varía, notificar antes
    
    # Recurrencia
    frequency = Column(Enum(RecurrenceFrequency), nullable=False)
    custom_frequency_days = Column(Integer, nullable=True)  # Para CUSTOM
    day_of_month = Column(Integer, nullable=True)  # 1-31 o -1 para último día
    day_of_week = Column(Integer, nullable=True)  # 1-7 para semanal
    
    # Periodo
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)  # Null = indefinido
    
    # Configuración
    auto_create = Column(Boolean, default=True)  # Crear automáticamente o solo recordar
    notify_before_days = Column(Integer, default=2)
    
    # Descripción
    merchant = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Estado
    is_active = Column(Boolean, default=True)
    last_created_date = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    account = relationship("Account")
    category = relationship("Category")
    transactions = relationship("Transaction", back_populates="recurring_transaction")

