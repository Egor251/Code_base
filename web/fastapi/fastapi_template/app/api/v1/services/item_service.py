"""
Сервис для работы с items (пример бизнес-логики).

Принципы:
1. Отделение бизнес-логики от роутеров
2. Работа только через модели и репозитории
3. Обработка ошибок на уровне сервиса
4. Легкое тестирование
"""

from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from app.api.v1.models.item import ItemCreate, ItemUpdate, ItemResponse
from app.core.database import Base
from app.exceptions import (
    ITEM_NOT_FOUND_ERROR,
    ITEM_ALREADY_EXISTS_ERROR,
    BusinessError,
    NotFoundError,
    ValidationError
)
import app.core.logging as logging

logger = logging.get_logger(__name__)

# Модель SQLAlchemy (обычно в отдельном файле models/db_models.py)
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


class ItemModel(Base):
    __tablename__ = "items"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(String(1000), nullable=True)
    price = Column(String(50), nullable=True)  # Используем String для гибкости
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ItemService:
    """
    Сервис для работы с items.

    Содержит всю бизнес-логику по работе с items.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_item(self, item_id: UUID) -> ItemResponse:
        """
        Получить item по ID.

        Args:
            item_id: UUID item'а

        Returns:
            ItemResponse: Данные item'а

        Raises:
            NotFoundError: Если item не найден
        """
        query = select(ItemModel).where(
            ItemModel.id == item_id,
            ItemModel.is_active == True
        )

        result = await self.db.execute(query)
        item = result.scalar_one_or_none()

        if not item:
            raise NotFoundError(f"Item with id {item_id} not found")

        return self._model_to_response(item)

    async def get_items(
            self,
            skip: int = 0,
            limit: int = 100,
            search: Optional[str] = None
    ) -> List[ItemResponse]:
        """
        Получить список items с пагинацией.

        Args:
            skip: Сколько пропустить
            limit: Максимальное количество
            search: Поиск по имени

        Returns:
            List[ItemResponse]: Список items
        """
        query = select(ItemModel).where(ItemModel.is_active == True)

        if search:
            query = query.where(ItemModel.name.ilike(f"%{search}%"))

        query = query.offset(skip).limit(limit).order_by(ItemModel.created_at.desc())

        result = await self.db.execute(query)
        items = result.scalars().all()

        return [self._model_to_response(item) for item in items]

    async def create_item(self, item_data: ItemCreate) -> ItemResponse:
        """
        Создать новый item.

        Args:
            item_data: Данные для создания

        Returns:
            ItemResponse: Созданный item

        Raises:
            BusinessError: Если произошла ошибка
        """
        try:
            # Проверяем уникальность (пример)
            existing_query = select(ItemModel).where(
                ItemModel.name == item_data.name,
                ItemModel.is_active == True
            )
            existing_result = await self.db.execute(existing_query)
            if existing_result.scalar_one_or_none():
                raise BusinessError(
                    message=f"Item with name '{item_data.name}' already exists",
                    code="ITEM_EXISTS"
                )

            # Создаем модель
            db_item = ItemModel(
                name=item_data.name,
                description=item_data.description,
                price=item_data.price,
                is_active=True
            )

            self.db.add(db_item)
            await self.db.commit()
            await self.db.refresh(db_item)

            logger.info(f"Item created: {db_item.id} - {db_item.name}")

            return self._model_to_response(db_item)

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating item: {e}")
            raise BusinessError(
                message="Failed to create item",
                code="CREATE_ERROR"
            )

    async def update_item(
            self,
            item_id: UUID,
            item_data: ItemUpdate
    ) -> ItemResponse:
        """
        Обновить существующий item.

        Args:
            item_id: UUID item'а
            item_data: Данные для обновления

        Returns:
            ItemResponse: Обновленный item

        Raises:
            NotFoundError: Если item не найден
            BusinessError: Если произошла ошибка
        """
        try:
            # Проверяем существование
            query = select(ItemModel).where(
                ItemModel.id == item_id,
                ItemModel.is_active == True
            )
            result = await self.db.execute(query)
            item = result.scalar_one_or_none()

            if not item:
                raise NotFoundError(f"Item with id {item_id} not found")

            # Обновляем поля
            update_data = item_data.dict(exclude_unset=True)
            if update_data:
                stmt = (
                    update(ItemModel)
                    .where(ItemModel.id == item_id)
                    .values(**update_data, updated_at=datetime.utcnow())
                )
                await self.db.execute(stmt)
                await self.db.commit()

                # Получаем обновленный item
                await self.db.refresh(item)

            logger.info(f"Item updated: {item_id}")

            return self._model_to_response(item)

        except NotFoundError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating item {item_id}: {e}")
            raise BusinessError(
                message="Failed to update item",
                code="UPDATE_ERROR"
            )

    async def delete_item(self, item_id: UUID) -> bool:
        """
        Удалить item (soft delete).

        Args:
            item_id: UUID item'а

        Returns:
            bool: True если удален

        Raises:
            NotFoundError: Если item не найден
            BusinessError: Если произошла ошибка
        """
        try:
            # Проверяем существование
            query = select(ItemModel).where(
                ItemModel.id == item_id,
                ItemModel.is_active == True
            )
            result = await self.db.execute(query)
            item = result.scalar_one_or_none()

            if not item:
                raise NotFoundError(f"Item with id {item_id} not found")

            # Soft delete
            stmt = (
                update(ItemModel)
                .where(ItemModel.id == item_id)
                .values(is_active=False, updated_at=datetime.utcnow())
            )
            await self.db.execute(stmt)
            await self.db.commit()

            logger.info(f"Item deleted (soft): {item_id}")

            return True

        except NotFoundError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting item {item_id}: {e}")
            raise BusinessError(
                message="Failed to delete item",
                code="DELETE_ERROR"
            )

    async def get_items_count(self, search: Optional[str] = None) -> int:
        """
        Получить общее количество items.

        Args:
            search: Поиск по имени

        Returns:
            int: Количество items
        """
        from sqlalchemy import func

        query = select(func.count(ItemModel.id)).where(ItemModel.is_active == True)

        if search:
            query = query.where(ItemModel.name.ilike(f"%{search}%"))

        result = await self.db.execute(query)
        return result.scalar()

    # Вспомогательные методы
    def _model_to_response(self, item: ItemModel) -> ItemResponse:
        """Конвертирует SQLAlchemy модель в Pydantic модель."""
        return ItemResponse(
            id=item.id,
            name=item.name,
            description=item.description,
            price=item.price,
            is_active=item.is_active,
            created_at=item.created_at,
            updated_at=item.updated_at
        )