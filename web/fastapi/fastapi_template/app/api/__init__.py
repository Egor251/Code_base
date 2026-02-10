"""
Пакет API слоя.
"""

# Экспортируем роутеры для удобного импорта
from app.api.v1.routers.admin import admin_router
from app.api.v1.routers.items import items_router
from app.api.v1.routers.health import health_router

__all__ = [
    "admin_router",
    "items_router",
    "health_router"
]