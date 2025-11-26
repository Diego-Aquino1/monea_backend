"""
Modelo de Categorías
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class CategoryType(str, enum.Enum):
    """Tipo de categoría"""
    EXPENSE = "expense"
    INCOME = "income"


class Category(Base):
    """Modelo de categoría para transacciones"""
    
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)  # Para subcategorías
    
    # Información básica
    name = Column(String, nullable=False)
    type = Column(Enum(CategoryType), nullable=False)
    
    # Personalización
    icon = Column(String, default="category")
    color = Column(String, default="#9E9E9E")
    
    # Configuración
    is_system = Column(Boolean, default=False)  # Categorías predefinidas
    is_hidden = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    subcategories = relationship("Category", backref="parent", remote_side=[id])
    transactions = relationship("Transaction", back_populates="category")

