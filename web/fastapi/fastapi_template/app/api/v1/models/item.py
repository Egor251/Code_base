"""
Pydantic модели для работы с items.
"""

from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, validator


class ItemBase(BaseModel):
    """Базовая модель item."""
    name: str = Field(..., min_length=1, max_length=255, description="Название item")
    description: Optional[str] = Field(None, max_length=1000, description="Описание")
    price: Optional[str] = Field(None, max_length=50, description="Цена")


class ItemCreate(ItemBase):
    """Модель для создания item."""
    pass


class ItemUpdate(BaseModel):
    """Модель для обновления item."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    price: Optional[str] = Field(None, max_length=50)

    @validator('name')
    def name_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Name cannot be empty')
        return v


class ItemInDB(ItemBase):
    """Модель item в БД."""
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Для работы с SQLAlchemy моделями


class ItemResponse(ItemInDB):
    """Модель ответа для item."""
    pass


class ItemListResponse(BaseModel):
    """Модель ответа для списка items."""
    items: list[ItemResponse]
    total: int
    page: int
    size: int
    pages: int