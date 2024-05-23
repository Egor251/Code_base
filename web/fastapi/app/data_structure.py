from enum import Enum
from typing import Optional
import re
from pydantic import BaseModel, Field, field_validator


class KeyEnum(Enum):
    registration = 'registration'
    new_message = 'new_message'
    new_post = 'new_post'
    new_login = 'new_login'


class PostCom(BaseModel):  # Паттерн для входящих данных /create

    user_id: str = Field(pattern=r'[0-9a-fA-F]{24}')
    target_id: Optional[str] = None

    @field_validator("target_id")  # Валидатор для поля target_id в /create
    @classmethod
    def validate_target_id(cls, value):
        pattern = re.compile("[0-9a-fA-F]{24}")
        if pattern.match(value):  # Если target_id не удовлетворяет паттерну возвращает None
            return value
        else:
            return None


class ReadCom(BaseModel):  # Паттерн для входящих данных /read
    user_id: str = Field(pattern=r'[0-9a-fA-F]{24}')
    notification_id: str = Field(pattern=r'[0-9a-fA-F]{24}')