"""
Modelo de Alertas y Notificaciones
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class AlertType(str, enum.Enum):
    """Tipo de alerta"""
    CREDIT_CARD_CUTOFF = "credit_card_cutoff"
    CREDIT_CARD_PAYMENT = "credit_card_payment"
    CREDIT_CARD_HIGH_USAGE = "credit_card_high_usage"
    BUDGET_WARNING = "budget_warning"
    BUDGET_EXCEEDED = "budget_exceeded"
    FIXED_EXPENSE = "fixed_expense"
    GOAL_CONTRIBUTION = "goal_contribution"
    GOAL_COMPLETED = "goal_completed"
    ANOMALY_DETECTED = "anomaly_detected"
    WEEKLY_SUMMARY = "weekly_summary"
    MONTHLY_REPORT = "monthly_report"
    NO_TRANSACTIONS_TODAY = "no_transactions_today"
    INVESTMENT_CHANGE = "investment_change"
    CUSTOM = "custom"


class AlertPriority(str, enum.Enum):
    """Prioridad de alerta"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Alert(Base):
    """Modelo de alerta/notificación"""
    
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Tipo y prioridad
    type = Column(Enum(AlertType), nullable=False)
    priority = Column(Enum(AlertPriority), default=AlertPriority.MEDIUM)
    
    # Contenido
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    
    # Enlaces a entidades relacionadas
    related_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    related_budget_id = Column(Integer, ForeignKey("budgets.id"), nullable=True)
    related_goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True)
    related_credit_card_id = Column(Integer, ForeignKey("credit_cards.id"), nullable=True)
    
    # Estado
    is_read = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    
    # Acción
    action_url = Column(String, nullable=True)  # Deep link a pantalla específica
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime, nullable=True)
    
    # Relaciones
    related_transaction = relationship("Transaction")
    related_budget = relationship("Budget")
    related_goal = relationship("Goal")
    related_credit_card = relationship("CreditCard")

