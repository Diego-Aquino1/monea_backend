"""
Modelos de Metas Financieras
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum, Date, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class GoalType(str, enum.Enum):
    """Tipo de meta"""
    SAVINGS = "savings"
    DEBT_PAYMENT = "debt_payment"
    INVESTMENT = "investment"
    NET_WORTH = "net_worth"


class GoalPriority(str, enum.Enum):
    """Prioridad de meta"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Goal(Base):
    """Modelo de meta financiera"""
    
    __tablename__ = "goals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Información básica
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    type = Column(Enum(GoalType), nullable=False)
    
    # Montos
    target_amount = Column(Float, nullable=False)
    initial_amount = Column(Float, default=0.0)
    current_amount = Column(Float, default=0.0)
    
    # Fechas
    target_date = Column(Date, nullable=True)  # Fecha objetivo (opcional)
    
    # Configuración
    linked_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    auto_contribution_amount = Column(Float, nullable=True)
    auto_contribution_frequency = Column(String, nullable=True)  # weekly, biweekly, monthly
    
    # Prioridad y personalización
    priority = Column(Enum(GoalPriority), default=GoalPriority.MEDIUM)
    color = Column(String, default="#4CAF50")
    icon = Column(String, default="flag")
    
    # Estado
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    is_archived = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    linked_account = relationship("Account")
    contributions = relationship("GoalContribution", back_populates="goal")


class GoalContribution(Base):
    """Aportación a una meta"""
    
    __tablename__ = "goal_contributions"
    
    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=False)
    
    amount = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)
    notes = Column(Text, nullable=True)
    is_automatic = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    goal = relationship("Goal", back_populates="contributions")

