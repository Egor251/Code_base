"""
Базовые Pydantic модели для стандартизации ответов API.

Принципы:
1. Все ответы в одном формате
2. Стандартные поля для пагинации, ошибок
3. Легко расширяемы
"""

from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel, Field
from datetime import datetime

DataT = TypeVar("DataT")


class BaseResponse(BaseModel):
    """Базовая модель ответа."""
    success: bool = Field(default=True, description="Успешность операции")
    message: Optional[str] = Field(None, description="Сообщение для пользователя")
    timestamp: datetime = Field(default_factory=datetime.now, description="Время ответа")


class SuccessResponse(BaseResponse):
    """Успешный ответ с данными."""
    data: Optional[Any] = Field(None, description="Данные ответа")


class ErrorResponse(BaseResponse):
    """Ответ с ошибкой."""
    success: bool = Field(default=False, description="Всегда false для ошибок")
    error: str = Field(..., description="Код ошибки")
    detail: Optional[str] = Field(None, description="Детальное описание ошибки")


class PaginatedResponse(BaseResponse, Generic[DataT]):
    """Ответ с пагинацией."""
    data: List[DataT] = Field(default_factory=list, description="Список данных")
    total: int = Field(..., description="Общее количество элементов")
    page: int = Field(..., description="Текущая страница")
    size: int = Field(..., description="Количество элементов на странице")
    pages: int = Field(..., description="Общее количество страниц")


# Примеры использования:
"""
# Успешный ответ с одним элементом
response = SuccessResponse(
    message="Элемент создан",
    data={"id": 1, "name": "Test"}
)

# Ошибка
response = ErrorResponse(
    error="NOT_FOUND",
    message="Элемент не найден",
    detail="Элемент с ID 123 не существует"
)

# Пагинированный ответ
response = PaginatedResponse[ItemModel](
    data=items,
    total=100,
    page=1,
    size=10,
    pages=10
)
"""