"""
Универсальный асинхронный сервис для обработки сообщений Kafka.
Поддерживает любые типы обработчиков с валидацией через Pydantic.
Обрабатывает сообщения строго по одному для гарантии порядка.
"""

import json
import sys
from typing import Any, Dict, Optional, Type
import asyncio
from datetime import datetime, timezone

import importlib
from loguru import logger
from pydantic import BaseModel, ValidationError
from aiokafka.structs import ConsumerRecord
import traceback

from kafka_class import KafkaBase  # Предполагается, что это ваш базовый класс


class GenericService(KafkaBase):
    """
    Универсальный сервис для обработки Kafka сообщений.

    Особенности:
    - Последовательная обработка сообщений (гарантия порядка)
    - Поддержка любых обработчиков через dependency injection
    - Валидация через Pydantic схемы
    - Отправка ошибок в отдельный топик
    - Ручное подтверждение сообщений
    """

    def __init__(
        self,
        processor_path: str,
        processor_class_name: str,
        validator_path: str,
        consumer_group: str = "generic-service-group",
        consumer_topic: str = "service-requests",
        producer_topic: str = "service-results",
        error_topic_suffix: str = "-errors",
        **kwargs
    ):
        """
        Инициализация сервиса.

        Args:
            processor_path: Путь к модулю с классом-обработчиком (например, 'services.processors.my_processor')
            processor_class_name: Имя класса-обработчика (например, 'MyProcessor')
            validator_path: Путь к модулю с Pydantic схемой валидации
            consumer_group: ID группы Kafka consumer
            consumer_topic: Топик для входящих сообщений
            producer_topic: Топик для исходящих результатов
            error_topic_suffix: Суффикс для топика ошибок
            **kwargs: Дополнительные параметры для базового Kafka класса
        """
        super().__init__(**kwargs)

        self.consumer_group = consumer_group
        self.consumer_topic = consumer_topic
        self.producer_topic = producer_topic
        self.error_topic = f"{self.producer_topic}{error_topic_suffix}"

        self._running = False

        # Загрузка обработчика и валидатора
        self.processor_class = self._load_component(processor_path, processor_class_name)
        self.validator_class = self._load_component(validator_path, "RequestSchema")

        logger.info(
            f"Service initialized: "
            f"processor={processor_class_name}, "
            f"consumer_topic={consumer_topic}, "
            f"producer_topic={producer_topic}"
        )

    @staticmethod
    def _load_component(module_path: str, class_name: str) -> Any:
        """
        Динамическая загрузка класса из модуля.

        Args:
            module_path: Путь к модулю (например, 'my_module.processor')
            class_name: Имя класса для загрузки

        Returns:
            Загруженный класс

        Raises:
            ImportError: Если не удалось загрузить модуль или класс
        """
        try:
            module = importlib.import_module(module_path)
            component_class = getattr(module, class_name)
            logger.debug(f"Successfully loaded {class_name} from {module_path}")
            return component_class
        except ModuleNotFoundError as e:
            logger.error(f"Module not found: {module_path}")
            raise ImportError(f"Failed to load module {module_path}: {e}")
        except AttributeError as e:
            logger.error(f"Class {class_name} not found in module {module_path}")
            raise ImportError(f"Class {class_name} not found in {module_path}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error loading {class_name} from {module_path}: {e}")
            raise

    async def _parse_and_validate(self, msg: ConsumerRecord) -> Dict[str, Any]:
        """
        Парсинг и валидация входящего сообщения.

        Args:
            msg: Сообщение от Kafka consumer

        Returns:
            Валидированные данные в виде словаря

        Raises:
            ValueError: При ошибке парсинга JSON или валидации
        """
        try:
            # Декодирование JSON
            raw_data = json.loads(msg.value.decode('utf-8'))

            # Валидация через Pydantic
            validated_data = self.validator_class(**raw_data)

            # Добавляем метаданные сообщения
            result = validated_data.dict()
            result["_metadata"] = {
                "topic": msg.topic,
                "partition": msg.partition,
                "offset": msg.offset,
                "timestamp": msg.timestamp / 1000 if msg.timestamp else None
            }

            return result

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
        except ValidationError as e:
            raise ValueError(f"Validation failed: {e.errors()}")
        except Exception as e:
            raise ValueError(f"Failed to parse message: {e}")

    async def _send_error(self, error: Exception, original_msg: ConsumerRecord, context: Optional[Dict] = None):
        """
        Отправка информации об ошибке в отдельный топик.

        Args:
            error: Исключение, которое произошло
            original_msg: Исходное сообщение Kafka
            context: Дополнительный контекст ошибки
        """
        error_info = {
            "error_type": error.__class__.__name__,
            "error_message": str(error),
            "original_message": original_msg.value.decode('utf-8') if original_msg.value else None,
            "message_metadata": {
                "topic": original_msg.topic,
                "partition": original_msg.partition,
                "offset": original_msg.offset,
                "key": original_msg.key.decode('utf-8') if original_msg.key else None
            },
            "traceback": traceback.format_exc(),
            "context": context or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        logger.error(f"Processing error: {error_info['error_type']} - {error_info['error_message']}")

        try:
            await self.send_message(
                topic=self.error_topic,
                value=error_info,
                headers={
                    "error_type": error_info["error_type"],
                    "original_topic": original_msg.topic,
                    "timestamp": error_info["timestamp"]
                }
            )
            logger.debug(f"Error sent to {self.error_topic}")
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")

    async def _process_message(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Основная логика обработки задачи.
        Должен быть переопределен в дочерних классах при необходимости.

        Args:
            task: Валидированная задача

        Returns:
            Результат обработки
        """
        # Создаем экземпляр обработчика
        processor = self.processor_class()

        # Извлекаем метод обработки (по умолчанию 'process')
        process_method = getattr(processor, "process", None)
        if not process_method or not callable(process_method):
            process_method = getattr(processor, "execute", None)

        if not process_method or not callable(process_method):
            raise AttributeError(
                f"Processor {self.processor_class.__name__} must have 'process' or 'execute' method"
            )

        # Вызываем метод обработки
        logger.info(f"Processing task with {self.processor_class.__name__}")
        result = await process_method(**task)

        return result

    async def start(self):
        """
        Запуск сервиса с последовательной обработкой сообщений.
        """
        self._running = True

        # Запускаем продюсера и консьюмера
        await self.start_producer()
        await self.start_consumer(
            topic=self.consumer_topic,
            group_id=self.consumer_group,
            enable_auto_commit=False,  # Ручное подтверждение
            auto_offset_reset="earliest"  # Читать с начала при первом запуске
        )

        logger.info(f"Service started. Listening to {self.consumer_topic}")
        logger.info(f"Results will be sent to {self.producer_topic}")
        logger.info(f"Errors will be sent to {self.error_topic}")

        try:
            async for msg in self._consumer:
                if not self._running:
                    break

                logger.debug(
                    f"Received message: topic={msg.topic}, "
                    f"partition={msg.partition}, offset={msg.offset}"
                )

                task_data = None
                try:
                    # Шаг 1: Парсинг и валидация
                    task_data = await self._parse_and_validate(msg)

                    # Шаг 2: Обработка
                    logger.info(f"Processing task: {task_data.get('task_id', 'unknown')}")
                    result = await self._process_message(task_data)

                    # Шаг 3: Формирование и отправка результата
                    response = {
                        "status": "completed",
                        "task_id": task_data.get("task_id"),
                        "processor": self.processor_class.__name__,
                        "result": result,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "metadata": task_data.get("_metadata", {})
                    }

                    await self.send_message(
                        topic=self.producer_topic,
                        value=response,
                        headers={
                            "processor_type": self.processor_class.__name__,
                            "task_id": str(task_data.get("task_id", "")),
                            "status": "success"
                        }
                    )

                    logger.info(f"Task {task_data.get('task_id', 'unknown')} completed successfully")

                    # Шаг 4: Подтверждение обработки
                    await self._consumer.commit()
                    logger.debug(f"Committed offset for task {task_data.get('task_id', 'unknown')}")

                except Exception as e:
                    logger.error(f"Failed to process message: {e}")

                    # Отправляем информацию об ошибке
                    await self._send_error(e, msg, {"task_data": task_data})

                    # Пропускаем сообщение с ошибкой (можно настроить политику повторений)
                    await self._consumer.commit()
                    logger.warning(f"Message committed despite error: {e}")

        except asyncio.CancelledError:
            logger.info("Service shutdown requested")
        except Exception as e:
            logger.critical(f"Unexpected error in message loop: {e}")
            raise
        finally:
            await self.stop()

    async def stop(self):
        """
        Корректное завершение работы сервиса.
        """
        self._running = False
        await super().stop()
        logger.info("Service stopped gracefully")


class ExampleValidator(BaseModel):
    """
    Пример Pydantic схемы для валидации входящих сообщений.
    Должен быть заменен на реальную схему в конкретном сервисе.
    """
    task_id: str
    data: Dict[str, Any]
    priority: Optional[int] = 1

    class Config:
        extra = "forbid"  # Запрещает дополнительные поля


class ExampleProcessor:
    """
    Пример класса-обработчика.
    Должен быть заменен на реальный обработчик в конкретном сервисе.
    """

    async def process(self, task_id: str, data: Dict[str, Any], priority: int = 1) -> Dict[str, Any]:
        """
        Основной метод обработки.

        Args:
            task_id: ID задачи
            data: Данные для обработки
            priority: Приоритет задачи

        Returns:
            Результат обработки
        """
        # Пример обработки
        logger.info(f"Processing task {task_id} with priority {priority}")

        # Имитация работы
        await asyncio.sleep(0.1)

        return {
            "processed_data": data,
            "status": "success",
            "task_id": task_id
        }


async def main():
    """
    Пример запуска сервиса с конфигурацией из переменных окружения или конфиг файла.
    """
    import os

    # Конфигурация (можно вынести в .env или конфиг файл)
    config = {
        "processor_path": os.getenv("PROCESSOR_PATH", "example.processor"),
        "processor_class": os.getenv("PROCESSOR_CLASS", "ExampleProcessor"),
        "validator_path": os.getenv("VALIDATOR_PATH", "example.validator"),
        "consumer_group": os.getenv("CONSUMER_GROUP", "example-service-group"),
        "consumer_topic": os.getenv("CONSUMER_TOPIC", "example-requests"),
        "producer_topic": os.getenv("PRODUCER_TOPIC", "example-results"),
        "kafka_servers": os.getenv("KAFKA_SERVERS", "localhost:9092"),
    }

    service = None
    try:
        service = GenericService(
            processor_path=config["processor_path"],
            processor_class_name=config["processor_class"],
            validator_path=config["validator_path"],
            consumer_group=config["consumer_group"],
            consumer_topic=config["consumer_topic"],
            producer_topic=config["producer_topic"],
            bootstrap_servers=config["kafka_servers"],
        )

        logger.info("Starting generic service...")
        await service.start()

    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.critical(f"Service failed to start: {e}")
        raise
    finally:
        if service:
            await service.stop()
        logger.info("Service shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown by keyboard interrupt")
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        sys.exit(1)