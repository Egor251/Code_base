"""
Точка входа в приложение FastAPI.

Основные принципы:
1. Создание приложения с метаданными
2. Настройка middleware (CORS, безопасность)
3. Подключение всех роутеров
4. Graceful startup/shutdown
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.config import settings
from app.api.v1.routers import (
    admin_router,
    items_router,
    health_router
)
from app.core.database import engine, Base
import app.core.logging as logging

# Инициализация логирования
logger = logging.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Контекст жизненного цикла приложения.

    Что происходит при запуске:
    1. Инициализация логирования
    2. Подключение к БД (если используется)
    3. Создание таблиц (в разработке)

    Что происходит при выключении:
    1. Закрытие подключений к БД
    2. Очистка ресурсов
    """
    # Startup
    logger.info("🚀 Starting FastAPI application")
    logger.info(f"📊 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🔧 Debug mode: {settings.DEBUG}")

    # Создание таблиц БД (только для разработки!)
    if settings.ENVIRONMENT == "development":
        logger.info("🗃️  Creating database tables...")
        async with engine.begin() as conn:
            # ВНИМАНИЕ: В продакшене используйте миграции (Alembic)
            # await conn.run_sync(Base.metadata.create_all)
            pass

    yield  # Приложение работает здесь

    # Shutdown
    logger.info("🛑 Shutting down application...")
    await engine.dispose()


# Создание экземпляра FastAPI приложения
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Минимальный универсальный шаблон FastAPI проекта",
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Middleware
# 1. CORS - разрешает запросы с фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # Или конкретные: ["GET", "POST", "PUT", "DELETE"]
    allow_headers=["*"],
)

# 2. TrustedHost - защита от host header атак
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)

# Подключение роутеров
# Порядок важен: сначала специфичные, потом общие
app.include_router(
    admin_router,
    prefix=f"{settings.API_V1_STR}/admin",
    tags=["admin"],
)

app.include_router(
    items_router,
    prefix=f"{settings.API_V1_STR}/items",
    tags=["items"],
)

app.include_router(
    health_router,
    prefix=f"{settings.API_V1_STR}/health",
    tags=["health"],
)


# Корневой endpoint
@app.get("/")
async def root():
    """
    Корневой endpoint.

    Используется для:
    1. Проверки, что приложение запущено
    2. Получения базовой информации
    3. Health check балансировщиков нагрузки
    """
    return {
        "message": f"{settings.PROJECT_NAME} is running",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs" if settings.DEBUG else None,
    }


# Запуск приложения (только для разработки)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,  # Автоматическая перезагрузка при изменениях
        log_level="info",
    )