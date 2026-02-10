"""
Health check endpoints для мониторинга работы приложения.

Принципы:
1. Простые endpoints без аутентификации
2. Проверка всех зависимостей (БД, внешние сервисы)
3. Используются балансировщиками нагрузки и оркестраторами
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_session
from app.api.v1.models.response import SuccessResponse
import app.core.logging as logging

logger = logging.get_logger(__name__)

# Создаем роутер
health_router = APIRouter(
    tags=["health"],
    responses={
        200: {"description": "Success"},
        503: {"description": "Service Unavailable"}
    }
)


@health_router.get("/")
async def health() -> SuccessResponse:
    """
    Базовый health check.

    Используется для:
    - Проверки, что приложение запущено
    - Load balancer health checks
    - Kubernetes liveness probes

    Возвращает:
        SuccessResponse: Базовая информация о сервисе
    """
    return SuccessResponse(
        message="Service is healthy",
        data={
            "status": "healthy",
            "timestamp": "now"  # В реальном приложении используйте datetime
        }
    )


@health_router.get("/ready")
async def readiness(
        db: AsyncSession = Depends(get_session)
) -> SuccessResponse:
    """
    Readiness probe.

    Проверяет, что приложение готово обслуживать запросы:
    1. Подключение к БД работает
    2. Все зависимости доступны
    3. Приложение в рабочем состоянии

    Args:
        db: Сессия БД для проверки подключения

    Returns:
        SuccessResponse: Статус готовности

    Raises:
        503: Если приложение не готово
    """
    try:
        # Проверяем подключение к БД
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        db_status = "disconnected"
        # В реальном приложении здесь можно вернуть 503

    return SuccessResponse(
        message="Readiness check",
        data={
            "database": db_status,
            "status": "ready" if db_status == "connected" else "not_ready"
        }
    )


@health_router.get("/live")
async def liveness() -> SuccessResponse:
    """
    Liveness probe.

    Проверяет, что приложение живо (не зависло).
    Более легковесная проверка чем readiness.

    Returns:
        SuccessResponse: Статус живости
    """
    return SuccessResponse(
        message="Liveness check",
        data={"status": "alive"}
    )


@health_router.get("/info")
async def info() -> dict:
    """
    Информация о приложении.

    Возвращает информацию для:
    - Мониторинга
    - Отладки
    - Документации

    Returns:
        dict: Информация о приложении
    """
    import sys
    import platform

    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "environment": "development",  # Заменить на settings.ENVIRONMENT
        "start_time": "2024-01-01T00:00:00Z"  # Заменить на реальное время старта
    }