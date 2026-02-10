"""
Админские роутеры API.

Принципы:
1. Только для администраторов
2. Защищены admin_auth зависимостью
3. Методы для управления приложением
"""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from typing import Any

from app.auth.admin import admin_auth
from app.config import settings
from app.api.v1.models.response import SuccessResponse
import app.core.logging as logging

logger = logging.get_logger(__name__)

# Создаем роутер с зависимостью аутентификации
admin_router = APIRouter(
    dependencies=[Depends(admin_auth)],  # Все endpoint'ы защищены
    tags=["admin"],
    responses={
        403: {"description": "Forbidden - Admin access required"},
        500: {"description": "Internal server error"}
    }
)


@admin_router.get("/config")
async def get_config() -> dict:
    """
    Получить конфигурацию приложения (без секретов).

    Используется для:
    - Отладки в production
    - Проверки конфигурации
    - Мониторинга

    Returns:
        dict: Конфигурация приложения с скрытыми секретами
    """
    return SuccessResponse(
        message="Application configuration",
        data=settings.get_safe_config()
    )


@admin_router.get("/status")
async def get_status() -> SuccessResponse:
    """
    Получить статус приложения.

    Более детальная информация чем health check.

    Returns:
        SuccessResponse: Статус приложения и метрики
    """
    import psutil
    import sys

    # Системные метрики
    process = psutil.Process()

    return SuccessResponse(
        message="Application status",
        data={
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "version": settings.VERSION,
            "system": {
                "cpu_percent": process.cpu_percent(),
                "memory_percent": process.memory_percent(),
                "threads": process.num_threads(),
                "uptime": process.create_time()
            },
            "python": {
                "version": sys.version,
                "implementation": sys.implementation.name
            }
        }
    )


@admin_router.get("/logs")
async def get_logs(
        level: str = Query("INFO", description="Уровень логирования"),
        limit: int = Query(100, ge=1, le=1000, description="Количество записей")
) -> SuccessResponse:
    """
    Получить последние логи приложения.

    ВНИМАНИЕ: В production нужно ограничить доступ к этому endpoint'у
    или реализовать ротацию логов.

    Args:
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR)
        limit: Максимальное количество записей

    Returns:
        SuccessResponse: Последние логи
    """
    # В реальном приложении читаем из файла логов
    # Здесь заглушка

    return SuccessResponse(
        message="Application logs",
        data={
            "level": level,
            "limit": limit,
            "logs": [
                f"Log entry {i}" for i in range(min(limit, 10))
            ]
        }
    )


@admin_router.post("/cache/clear")
async def clear_cache() -> SuccessResponse:
    """
    Очистить кэш приложения.

    В базовой реализации ничего не делает.
    В реальном приложении может очищать:
    - Redis cache
    - Memory cache
    - CDN cache
    """
    logger.warning("Cache clear requested by admin")

    # Заглушка - в реальном приложении очищаем кэш

    return SuccessResponse(
        message="Cache cleared",
        data={"status": "success"}
    )


@admin_router.get("/users")
async def list_users(
        active_only: bool = Query(True, description="Только активные пользователи")
) -> SuccessResponse:
    """
    Получить список пользователей (заглушка).

    В реальном приложении возвращает список пользователей из БД.
    """
    # Заглушка
    users = [
        {"id": 1, "username": "admin", "role": "admin", "active": True},
        {"id": 2, "username": "user1", "role": "user", "active": True},
    ]

    if active_only:
        users = [u for u in users if u["active"]]

    return SuccessResponse(
        message="Users list",
        data={
            "users": users,
            "count": len(users)
        }
    )


@admin_router.post("/maintenance/{action}")
async def maintenance_mode(
        action: str,
        message: str = Query("Maintenance in progress", description="Сообщение для пользователей")
) -> SuccessResponse:
    """
    Включить/выключить режим обслуживания.

    Args:
        action: enable или disable
        message: Сообщение для пользователей

    Returns:
        SuccessResponse: Результат операции
    """
    if action not in ["enable", "disable"]:
        return SuccessResponse(
            success=False,
            message="Invalid action",
            data={"valid_actions": ["enable", "disable"]}
        )

    logger.warning(f"Maintenance mode {action}d: {message}")

    # В реальном приложении:
    # 1. Устанавливаем флаг в Redis/БД
    # 2. Возвращаем 503 на все запросы кроме админских
    # 3. Уведомляем пользователей

    return SuccessResponse(
        message=f"Maintenance mode {action}d",
        data={
            "action": action,
            "message": message,
            "status": "active" if action == "enable" else "inactive"
        }
    )