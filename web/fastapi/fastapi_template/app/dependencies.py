"""
Dependency Injection контейнер для приложения.

Принципы:
1. Централизованное управление зависимостями
2. Ленивая инициализация
3. Легкое тестирование с моками
4. Единая точка конфигурации
"""

from typing import AsyncGenerator, Optional
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_session
from app.core.logging import get_logger
from app.auth import api_key_auth, admin_auth

logger = get_logger(__name__)


# === Базовые зависимости ===

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для получения сессии БД.

    Использование:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async for session in get_session():
        yield session


def get_settings():
    """
    Dependency для получения настроек приложения.

    Использование:
        @router.get("/config")
        async def get_config(settings: Settings = Depends(get_settings)):
            ...
    """
    return settings


# === Валидационные зависимости ===

class PaginationParams:
    """
    Dependency для пагинации.

    Автоматически парсит параметры page и size из query string.
    Проверяет лимиты.

    Использование:
        @router.get("/items")
        async def get_items(pagination: PaginationParams = Depends()):
            skip = (pagination.page - 1) * pagination.size
            limit = pagination.size
    """

    def __init__(
            self,
            page: int = 1,
            size: int = 20
    ):
        self.page = max(1, page)
        self.size = min(max(1, size), 100)  # Максимум 100 элементов на странице
        self.skip = (self.page - 1) * self.size


class FilterParams:
    """
    Dependency для фильтрации.

    Базовый класс для фильтров. Можно расширять под конкретные сущности.
    """

    def __init__(
            self,
            q: Optional[str] = None,  # Общий поиск
            sort_by: Optional[str] = None,
            sort_order: str = "asc"
    ):
        self.q = q
        self.sort_by = sort_by
        self.sort_order = sort_order if sort_order in ["asc", "desc"] else "asc"


# === Бизнес-зависимости ===

class ServiceContainer:
    """
    Контейнер для бизнес-сервисов.

    Инициализирует сервисы один раз и предоставляет их как зависимости.
    """

    def __init__(self):
        self._services = {}

    def get_service(self, service_class):
        """
        Возвращает экземпляр сервиса, создавая его при первом вызове.
        """
        if service_class not in self._services:
            self._services[service_class] = service_class()

        return self._services[service_class]


# Глобальный контейнер сервисов
_service_container = ServiceContainer()


def get_service(service_class):
    """
    Dependency для получения сервиса из контейнера.

    Использование:
        @router.get("/items")
        async def get_items(
            item_service: ItemService = Depends(get_service(ItemService))
        ):
            ...
    """

    def _get_service():
        return _service_container.get_service(service_class)

    return _get_service


# === Пользовательские зависимости ===

async def get_current_user(
        request: Request,
        client_id: str = Depends(api_key_auth)
) -> dict:
    """
    Dependency для получения текущего пользователя.

    В базовой реализации возвращает идентификатор клиента.
    Можно расширить для полноценной пользовательской системы.

    Использование:
        @router.get("/profile")
        async def get_profile(user: dict = Depends(get_current_user)):
            ...
    """
    return {
        "client_id": client_id,
        "ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent")
    }


async def get_admin_user(
        request: Request,
        _: None = Depends(admin_auth)
) -> dict:
    """
    Dependency для получения администратора.
    """
    return {
        "role": "admin",
        "ip": request.client.host if request.client else None
    }


# === Редкие зависимости ===

async def rate_limiter(
        request: Request,
        client_id: str = Depends(api_key_auth)
) -> None:
    """
    Dependency для rate limiting.

    В базовой реализации ничего не делает.
    Можно интегрировать с Redis или другими системами.

    Пример реализации с Redis:
        key = f"rate_limit:{client_id}:{request.url.path}"
        current = await redis.incr(key)
        if current == 1:
            await redis.expire(key, 60)  # Сброс через 60 секунд

        if current > 100:  # 100 запросов в минуту
            raise TOO_MANY_REQUESTS_ERROR
    """
    # Базовая реализация - всегда пропускает
    # Для production нужно добавить реальный rate limiting
    pass


async def request_logger(request: Request) -> None:
    """
    Dependency для логирования запросов.

    Логирует информацию о входящих запросах.
    """
    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"from {request.client.host if request.client else 'unknown'}"
    )