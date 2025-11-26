"""
Schemas de Usuario
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base de usuario"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Crear usuario"""
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    """Login de usuario"""
    username: str
    password: str


class UserUpdate(BaseModel):
    """Actualizar usuario"""
    full_name: Optional[str] = None
    base_currency: Optional[str] = None
    date_format: Optional[str] = None
    first_day_of_week: Optional[int] = Field(None, ge=1, le=7)
    financial_month_start_day: Optional[int] = Field(None, ge=1, le=31)
    theme: Optional[str] = None
    accent_color: Optional[str] = None
    enable_biometric: Optional[bool] = None
    pin_code: Optional[str] = None
    hide_amounts: Optional[bool] = None
    enable_notifications: Optional[bool] = None
    notification_time: Optional[str] = None


class UserResponse(UserBase):
    """Respuesta de usuario"""
    id: int
    base_currency: str
    date_format: str
    theme: str
    accent_color: str
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token de acceso"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

