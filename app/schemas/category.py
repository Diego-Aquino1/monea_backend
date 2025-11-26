"""
Schemas de Categorías
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.category import CategoryType


class CategoryBase(BaseModel):
    """Base de categoría"""
    name: str = Field(..., min_length=1, max_length=100)
    type: CategoryType
    icon: Optional[str] = "category"
    color: Optional[str] = "#9E9E9E"
    parent_id: Optional[int] = None


class CategoryCreate(CategoryBase):
    """Crear categoría"""
    pass


class CategoryUpdate(BaseModel):
    """Actualizar categoría"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    icon: Optional[str] = None
    color: Optional[str] = None
    is_hidden: Optional[bool] = None
    display_order: Optional[int] = None


class CategoryResponse(CategoryBase):
    """Respuesta de categoría"""
    id: int
    user_id: int
    is_system: bool
    is_hidden: bool
    display_order: int
    created_at: datetime
    
    # Subcategorías
    subcategories: Optional[List["CategoryResponse"]] = None
    
    class Config:
        from_attributes = True

