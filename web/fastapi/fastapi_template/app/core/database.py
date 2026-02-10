"""
Подключение к базе данных с использованием SQLAlchemy.

Принципы:
1. Асинхронная работа с БД
2. Connection pooling для производительности
3. Единая точка подключения
4. Корректное закрытие соединений
"""

from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import QueuePool

from app.config import settings
import app.core.logging as logging

logger = logging.get_logger(__name__)

# Базовый класс для моделей SQLAlchemy
# Все модели должны наследоваться от этого класса
Base = declarative_base()

# Глобальные переменные для engine и session factory
# Инициализируются при первом использовании
_engine: Optional[AsyncEngine] = None
_async_session_factory: Optional[async_sessionmaker] = None


def get_engine() -> AsyncEngine:
    """
    Возвращает engine для подключения к БД.

    Создается один раз при первом вызове (singleton pattern).
    Использует connection pooling для эффективного управления соединениями.

    Returns:
        AsyncEngine: Асинхронный engine SQLAlchemy
    """
    global _engine

    if _engine is None:
        if not settings.DATABASE_URL:
            raise ValueError("DATABASE_URL не указан в настройках")

        # Создаем асинхронный engine
        _engine = create_async_engine(
            str(settings.DATABASE_URL),
            echo=settings.DEBUG,  # Логировать SQL запросы в debug режиме
            poolclass=QueuePool,  # Используем пул соединений
            pool_size=20,  # Максимальное количество соединений в пуле
            max_overflow=10,  # Максимум дополнительных соединений при нагрузке
            pool_pre_ping=True,  # Проверять соединения перед использованием
            pool_recycle=3600,  # Пересоздавать соединения каждый час
        )

        logger.info("✅ Database engine initialized")

    return _engine


def get_session_factory() -> async_sessionmaker:
    """
    Возвращает фабрику для создания сессий БД.

    Returns:
        async_sessionmaker: Фабрика асинхронных сессий
    """
    global _async_session_factory

    if _async_session_factory is None:
        engine = get_engine()
        _async_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,  # Не удалять объекты после коммита
            autoflush=False,  # Не выполнять flush автоматически
        )

    return _async_session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для получения сессии БД.

    Использование в endpoint:
        async def some_endpoint(db: AsyncSession = Depends(get_session)):
            # работа с БД через db
            ...

    Yields:
        AsyncSession: Асинхронная сессия SQLAlchemy

    Гарантирует:
    1. Сессия будет закрыта после использования
    2. В случае ошибки будет выполнен rollback
    3. Не нужно явно закрывать сессию
    """
    session_factory = get_session_factory()

    async with session_factory() as session:
        try:
            yield session
            await session.commit()  # Автоматический коммит если нет ошибок
        except Exception:
            await session.rollback()  # Откат при ошибке
            raise
        finally:
            await session.close()  # Всегда закрываем сессию


async def disconnect() -> None:
    """
    Закрывает все соединения с БД.

    Вызывается при остановке приложения.
    """
    global _engine

    if _engine:
        await _engine.dispose()
        _engine = None
        _async_session_factory = None
        logger.info("✅ Database connections closed")


# Глобальные переменные для удобства
engine = get_engine()
SessionLocal = get_session_factory()