"""
Modelos de Inversiones
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum, Date, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class InvestmentType(str, enum.Enum):
    """Tipo de inversión"""
    STOCK = "stock"
    ETF = "etf"
    MUTUAL_FUND = "mutual_fund"
    CRYPTO = "crypto"
    BOND = "bond"
    REAL_ESTATE = "real_estate"
    OTHER = "other"


class InvestmentTransactionType(str, enum.Enum):
    """Tipo de transacción de inversión"""
    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"
    SPLIT = "split"
    ADJUSTMENT = "adjustment"


class Investment(Base):
    """Modelo de activo de inversión"""
    
    __tablename__ = "investments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Información del activo
    name = Column(String, nullable=False)
    ticker = Column(String, nullable=True)  # Símbolo (AAPL, BTC, etc.)
    type = Column(Enum(InvestmentType), nullable=False)
    
    # Cantidades
    quantity = Column(Float, default=0.0)  # Unidades/acciones
    purchase_price = Column(Float, nullable=False)  # Precio de compra unitario
    current_price = Column(Float, nullable=False)  # Precio actual unitario
    
    # Fechas
    purchase_date = Column(Date, nullable=False)
    last_price_update = Column(DateTime, nullable=True)
    
    # Información adicional
    broker_account = Column(String, nullable=True)  # Dónde está custodiado
    currency = Column(String, default="MXN")
    notes = Column(Text, nullable=True)
    
    # Estado
    is_active = Column(Boolean, default=True)  # False si se vendió completamente
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    transactions = relationship("InvestmentTransaction", back_populates="investment")


class InvestmentTransaction(Base):
    """Transacción de inversión (compra, venta, dividendo)"""
    
    __tablename__ = "investment_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    investment_id = Column(Integer, ForeignKey("investments.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Tipo de transacción
    type = Column(Enum(InvestmentTransactionType), nullable=False)
    
    # Detalles
    quantity = Column(Float, nullable=True)  # Para compras/ventas
    price_per_unit = Column(Float, nullable=True)
    total_amount = Column(Float, nullable=False)
    
    # Fecha
    date = Column(Date, nullable=False)
    
    # Información adicional
    fees = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    investment = relationship("Investment", back_populates="transactions")

