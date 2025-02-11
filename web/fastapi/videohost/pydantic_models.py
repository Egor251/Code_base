"""
Pydantic схемы
"""

from pydantic import BaseModel
from datetime import datetime


# Pydantic схемы
class VideoCreate(BaseModel):
    """
    Схема для создания видео

    Attributes:
        title (str): Заголовок видео
        description (str): Описание
    """
    title: str
    description: str


class VideoResponse(VideoCreate):
    """
    Схема для ответа о видео

    Attributes:
        id (int): Идентификатор
        created_at (datetime): Дата создания
        file_size (int): Размер файла
        duration (int): Длительность видео
    """
    id: int
    created_at: datetime
    file_size: int
    duration: int
