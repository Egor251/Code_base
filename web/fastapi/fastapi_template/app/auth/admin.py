"""
Аутентификация для административных endpoints.

Принципы:
1. Простая аутентификация по API ключу
2. Ключ передается в заголовке X-Admin-API-Key
3. Подходит для внутренних инструментов и админки
4. Не использовать для пользовательской аутентификации!
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from app.config import settings
from app.exceptions import FORBIDDEN_ERROR

# Заголовок для админского API ключа
ADMIN_API_KEY_HEADER = APIKeyHeader(
    name="X-Admin-API-Key",
    auto_error=False,  # Не выбрасывать ошибку автоматически
    description="Админский API ключ. Получить у администратора системы.",
    scheme_name="AdminAPIKey"
)


async def admin_auth(
        admin_api_key: str = Depends(ADMIN_API_KEY_HEADER)
) -> None:
    """
    Dependency для аутентификации администратора.

    Как работает:
    1. FastAPI автоматически извлекает заголовок X-Admin-API-Key
    2. Если заголовок отсутствует - возвращается 403
    3. Если ключ неверный - возвращается 403
    4. Если все ок - запрос проходит дальше

    Args:
        admin_api_key: API ключ из заголовка X-Admin-API-Key

    Raises:
        HTTPException: 403 если аутентификация не пройдена

    Пример использования в роутере:
        @router.get("/admin/endpoint", dependencies=[Depends(admin_auth)])
        async def admin_endpoint():
            ...
    """
    # Проверяем наличие ключа
    if not admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin API key is required"
        )

    # Проверяем валидность ключа
    if admin_api_key != settings.ADMIN_API_KEY:
        raise FORBIDDEN_ERROR

    # Если дошли сюда - аутентификация пройдена
    # Можно добавить дополнительную логику:
    # - Логирование доступа
    # - Проверка IP адреса
    # - Rate limiting