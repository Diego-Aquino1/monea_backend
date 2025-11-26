"""
Modelo de Usuario
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """Modelo de usuario del sistema"""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    
    # Configuración de usuario
    base_currency = Column(String, default="MXN")
    date_format = Column(String, default="DD/MM/YYYY")
    first_day_of_week = Column(Integer, default=1)  # 1=Lunes
    financial_month_start_day = Column(Integer, default=1)
    
    # Preferencias
    theme = Column(String, default="auto")  # light, dark, auto
    accent_color = Column(String, default="#2196F3")
    enable_biometric = Column(Boolean, default=False)
    pin_code = Column(String, nullable=True)
    hide_amounts = Column(Boolean, default=False)
    
    # Notificaciones
    enable_notifications = Column(Boolean, default=True)
    notification_time = Column(String, default="20:00")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)

