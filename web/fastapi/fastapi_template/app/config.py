"""
Конфигурация приложения через переменные окружения.

Принципы:
1. Все настройки через .env файл
2. Валидация при загрузке
3. Безопасное хранение секретов
4. Разные настройки для разных окружений
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator, PostgresDsn, AnyHttpUrl


class Settings(BaseSettings):
    """
    Настройки приложения.

    Pydantic автоматически загружает значения:
    1. Из переменных окружения
    2. Из .env файла
    3. Значений по умолчанию

    Важно: Имена переменных окружения должны быть в верхнем регистре.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,  # Чувствительность к регистру
        extra="ignore",  # Игнорировать лишние переменные
    )

    # === Основные настройки ===
    PROJECT_NAME: str = Field(default="FastAPI Template", env="PROJECT_NAME")
    VERSION: str = Field(default="1.0.0", env="VERSION")
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")

    # === Сервер ===
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    API_V1_STR: str = Field(default="/api/v1", env="API_V1_STR")

    # === Безопасность ===
    SECRET_KEY: str = Field(default="", env="SECRET_KEY")
    ADMIN_API_KEY: str = Field(default="", env="ADMIN_API_KEY")
    API_KEY: str = Field(default="", env="API_KEY")

    # 60 минут * 24 часа * 8 дней = 8 дней
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24 * 8, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    # === CORS (Cross-Origin Resource Sharing) ===
    # Список доменов, которым разрешено делать запросы
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = Field(
        default=["http://localhost:3000"],  # React/Vue dev server
        env="BACKEND_CORS_ORIGINS"
    )

    # === Хосты ===
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        env="ALLOWED_HOSTS"
    )

    # === База данных ===
    # Формат: postgresql+asyncpg://user:password@host:port/dbname
    DATABASE_URL: Optional[PostgresDsn] = Field(default=None, env="DATABASE_URL")

    # === Валидаторы ===
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        """
        Преобразует строку с разделителями в список URL.

        Пример переменной окружения:
        BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8080
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        """
        Проверяет, что SECRET_KEY установлен в продакшене.

        В разработке можно использовать дефолтное значение,
        но в продакшене это критическая уязвимость.
        """
        if not v and os.getenv("ENVIRONMENT") == "production":
            raise ValueError("SECRET_KEY must be set in production")
        return v or "development-secret-key-change-in-production"

    @validator("ADMIN_API_KEY")
    def validate_admin_key(cls, v):
        """Проверяет админский ключ."""
        if not v and os.getenv("ENVIRONMENT") == "production":
            raise ValueError("ADMIN_API_KEY must be set in production")
        return v or "admin-key-for-development"

    @validator("DEBUG", always=True)
    def set_debug_based_on_environment(cls, v, values):
        """
        Автоматически устанавливает DEBUG=True для development окружения.

        Это удобно: не нужно явно указывать DEBUG=true в .env файле.
        """
        environment = values.get("ENVIRONMENT", "development")
        return v or (environment == "development")

    # === Методы ===
    def is_development(self) -> bool:
        """Проверяет, что окружение - разработка."""
        return self.ENVIRONMENT == "development"

    def is_production(self) -> bool:
        """Проверяет, что окружение - продакшен."""
        return self.ENVIRONMENT == "production"

    def is_testing(self) -> bool:
        """Проверяет, что окружение - тестирование."""
        return self.ENVIRONMENT == "testing"

    def get_safe_config(self) -> dict:
        """
        Возвращает безопасную версию конфига без секретов.

        Используется для отладки и логов. Все секреты заменяются на ***.
        """
        config = self.model_dump()
        secrets = ["SECRET_KEY", "ADMIN_API_KEY", "API_KEY", "DATABASE_URL"]

        for secret in secrets:
            if secret in config and config[secret]:
                config[secret] = "***HIDDEN***"

        return config


# Глобальный экземпляр настроек
settings = Settings()

# Логирование загруженной конфигурации (без секретов)
if settings.DEBUG:
    import json

    safe_config = settings.get_safe_config()
    print("📋 Loaded configuration:")
    print(json.dumps(safe_config, indent=2, ensure_ascii=False))