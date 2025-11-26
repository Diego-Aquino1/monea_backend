"""
Modelo de Presupuestos
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class BudgetType(str, enum.Enum):
    """Tipo de presupuesto"""
    CATEGORY = "category"
    TAG = "tag"
    GLOBAL = "global"
    ACCOUNT = "account"


class BudgetPeriod(str, enum.Enum):
    """Periodo de presupuesto"""
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    ANNUAL = "annual"


class Budget(Base):
    """Modelo de presupuesto"""
    
    __tablename__ = "budgets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Información básica
    name = Column(String, nullable=False)
    type = Column(Enum(BudgetType), nullable=False)
    
    # Configuración
    limit_amount = Column(Float, nullable=False)
    period = Column(Enum(BudgetPeriod), nullable=False)
    start_day = Column(Integer, default=1)  # Día de inicio del periodo
    
    # Rollover
    enable_rollover = Column(Boolean, default=False)
    rollover_max_accumulation = Column(Float, nullable=True)  # Máximo a acumular
    current_rollover = Column(Float, default=0.0)
    
    # Alertas
    alert_at_percentage = Column(Float, default=80.0)
    alert_on_exceed = Column(Boolean, default=True)
    
    # Filtros (según tipo)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    tag = Column(String, nullable=True)
    
    # Estado
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    category = relationship("Category")
    account = relationship("Account")

