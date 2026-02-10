"""
Аутентификация по API ключу для клиентов/сервисов.

Принципы:
1. Простая аутентификация для machine-to-machine коммуникации
2. Ключ передается в заголовке X-API-Key
3. Можно расширить для поддержки множества клиентов
"""

from typing import Optional
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

from app.config import settings
from app.exceptions import FORBIDDEN_ERROR, UNAUTHORIZED_ERROR

# Заголовок для клиентского API ключа
API_KEY_HEADER = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
    description="API ключ для доступа к сервису",
    scheme_name="APIKey"
)


async def api_key_auth(
        api_key: Optional[str] = Depends(API_KEY_HEADER)
) -> str:
    """
    Dependency для аутентификации по API ключу.

    Возвращает идентификатор клиента (если используется несколько ключей).
    В базовой реализации просто проверяет один ключ.

    Args:
        api_key: API ключ из заголовка X-API-Key

    Returns:
        str: Идентификатор клиента (в данном случае "default")

    Raises:
        HTTPException: 401/403 если аутентификация не пройдена
    """
    # Проверяем наличие ключа
    if not api_key:
        raise UNAUTHORIZED_ERROR

    # Проверяем валидность ключа
    if api_key != settings.API_KEY:
        raise FORBIDDEN_ERROR

    # Возвращаем идентификатор клиента
    # В реальном приложении можно:
    # 1. Хранить ключи в БД
    # 2. Возвращать client_id
    # 3. Проверять permissions
    return "default"


async def optional_api_key_auth(
        api_key: Optional[str] = Depends(API_KEY_HEADER)
) -> Optional[str]:
    """
    Optional dependency для аутентификации.

    Позволяет endpoint'ам работать как с аутентификацией, так и без.
    Полезно для:
    - Публичных API с ограниченным доступом для авторизованных
    - Демо endpoints

    Returns:
        Optional[str]: client_id если ключ валидный, иначе None
    """
    if not api_key or api_key != settings.API_KEY:
        return None

    return "default"