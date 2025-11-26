"""
Endpoints de categorías
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.category import Category, CategoryType
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.utils.security import get_current_active_user

router = APIRouter()


def create_default_categories(db: Session, user_id: int):
    """Crear categorías predeterminadas para nuevo usuario"""
    default_categories = [
        # Gastos
        {"name": "Alimentación", "type": CategoryType.EXPENSE, "icon": "restaurant", "color": "#FF5722"},
        {"name": "Transporte", "type": CategoryType.EXPENSE, "icon": "directions_car", "color": "#2196F3"},
        {"name": "Hogar", "type": CategoryType.EXPENSE, "icon": "home", "color": "#4CAF50"},
        {"name": "Entretenimiento", "type": CategoryType.EXPENSE, "icon": "movie", "color": "#9C27B0"},
        {"name": "Salud", "type": CategoryType.EXPENSE, "icon": "local_hospital", "color": "#F44336"},
        {"name": "Educación", "type": CategoryType.EXPENSE, "icon": "school", "color": "#FF9800"},
        {"name": "Ropa", "type": CategoryType.EXPENSE, "icon": "shopping_bag", "color": "#E91E63"},
        {"name": "Tecnología", "type": CategoryType.EXPENSE, "icon": "devices", "color": "#00BCD4"},
        {"name": "Finanzas", "type": CategoryType.EXPENSE, "icon": "account_balance", "color": "#607D8B"},
        {"name": "Regalos", "type": CategoryType.EXPENSE, "icon": "card_giftcard", "color": "#FFC107"},
        {"name": "Otros Gastos", "type": CategoryType.EXPENSE, "icon": "more_horiz", "color": "#9E9E9E"},
        # Ingresos
        {"name": "Salario", "type": CategoryType.INCOME, "icon": "work", "color": "#4CAF50"},
        {"name": "Freelance", "type": CategoryType.INCOME, "icon": "business_center", "color": "#8BC34A"},
        {"name": "Inversiones", "type": CategoryType.INCOME, "icon": "trending_up", "color": "#CDDC39"},
        {"name": "Otros Ingresos", "type": CategoryType.INCOME, "icon": "attach_money", "color": "#9E9E9E"},
    ]
    
    for cat_data in default_categories:
        category = Category(
            user_id=user_id,
            name=cat_data["name"],
            type=cat_data["type"],
            icon=cat_data["icon"],
            color=cat_data["color"],
            is_system=True,
        )
        db.add(category)
    
    db.commit()


@router.get("", response_model=List[CategoryResponse])
def get_categories(
    type: CategoryType = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener categorías del usuario"""
    query = db.query(Category).filter(
        Category.user_id == current_user.id,
        Category.is_hidden == False
    )
    
    if type:
        query = query.filter(Category.type == type)
    
    categories = query.order_by(Category.display_order, Category.name).all()
    return categories


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Crear nueva categoría"""
    category = Category(
        user_id=current_user.id,
        name=category_data.name,
        type=category_data.type,
        icon=category_data.icon,
        color=category_data.color,
        parent_id=category_data.parent_id,
    )
    
    db.add(category)
    db.commit()
    db.refresh(category)
    
    return category


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category_update: CategoryUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Actualizar categoría"""
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id
    ).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    update_data = category_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)
    
    db.commit()
    db.refresh(category)
    
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Eliminar categoría"""
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id
    ).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    if category.is_system:
        raise HTTPException(
            status_code=400,
            detail="No se pueden eliminar categorías del sistema. Usa ocultar en su lugar."
        )
    
    db.delete(category)
    db.commit()

