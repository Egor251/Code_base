"""
Универсальный асинхронный сервис для параллельной обработки сообщений Kafka.
Поддерживает пул воркеров для обработки задач с гарантией порядка в рамках партиции.
"""

import json
import sys
from typing import Any, Dict, Optional, List
import asyncio
from datetime import datetime, timezone

import importlib
from loguru import logger
from pydantic import BaseModel, ValidationError
from aiokafka.structs import ConsumerRecord
import traceback

from kafka_class import KafkaBase


class ParallelProcessorService(KafkaBase):
    """
    Универсальный сервис для параллельной обработки Kafka сообщений.

    Особенности:
    - Пул воркеров для параллельной обработки
    - Сохранение порядка в рамках партиции
    - Настраиваемое количество воркеров
    - Graceful shutdown
    """

    def __init__(
        self,
        processor_path: str,
        processor_class_name: str,
        validator_path: str,
        consumer_group: str = "parallel-service-group",
        consumer_topic: str = "service-requests",
        producer_topic: str = "service-results",
        max_workers: int = 5,
        error_topic_suffix: str = "-errors",
        queue_size: Optional[int] = None,
        **kwargs
    ):
        """
        Инициализация сервиса с поддержкой параллельной обработки.

        Args:
            processor_path: Путь к модулю с классом-обработчиком
            processor_class_name: Имя класса-обработчика
            validator_path: Путь к модулю с Pydantic схемой
            consumer_group: ID группы Kafka consumer
            consumer_topic: Топик для входящих сообщений
            producer_topic: Топик для исходящих результатов
            max_workers: Максимальное количество параллельных воркеров
            error_topic_suffix: Суффикс для топика ошибок
            queue_size: Максимальный размер очереди задач (None = max_workers * 2)
            **kwargs: Дополнительные параметры для KafkaBase
        """
        super().__init__(**kwargs)

        self.consumer_group = consumer_group
        self.consumer_topic = consumer_topic
        self.producer_topic = producer_topic
        self.error_topic = f"{self.producer_topic}{error_topic_suffix}"
        self.max_workers = max_workers
        self.queue_size = queue_size or (max_workers * 2)

        # Очередь задач для воркеров
        self.task_queue = asyncio.Queue(maxsize=self.queue_size)
        self._running = False
        self.workers: List[asyncio.Task] = []

        # Загрузка обработчика и валидатора
        self.processor_class = self._load_component(processor_path, processor_class_name)
        self.validator_class = self._load_component(validator_path, "RequestSchema")

        logger.info(
            f"Parallel service initialized: "
            f"workers={max_workers}, "
            f"queue_size={self.queue_size}, "
            f"processor={processor_class_name}"
        )

    @staticmethod
    def _load_component(module_path: str, class_name: str) -> Any:
        """Динамическая загрузка класса из модуля."""
        try:
            module = importlib.import_module(module_path)
            component_class = getattr(module, class_name)
            logger.debug(f"Loaded {class_name} from {module_path}")
            return component_class
        except ModuleNotFoundError as e:
            logger.error(f"Module not found: {module_path}")
            raise ImportError(f"Failed to load module {module_path}: {e}")
        except AttributeError as e:
            logger.error(f"Class {class_name} not found in module {module_path}")
            raise ImportError(f"Class {class_name} not found in {module_path}: {e}")
        except Exception as e:
            logger.error(f"Error loading {class_name} from {module_path}: {e}")
            raise

    async def _parse_and_validate(self, msg: ConsumerRecord) -> Dict[str, Any]:
        """
        Парсинг и валидация входящего сообщения.

        Returns:
            Валидированные данные с метаданными сообщения
        """
        try:
            raw_data = json.loads(msg.value.decode('utf-8'))
            validated_data = self.validator_class(**raw_data)

            result = validated_data.dict()
            result["_metadata"] = {
                "kafka_topic": msg.topic,
                "partition": msg.partition,
                "offset": msg.offset,
                "key": msg.key.decode('utf-8') if msg.key else None,
                "timestamp": datetime.fromtimestamp(msg.timestamp / 1000, timezone.utc)
                if msg.timestamp else None
            }

            return result

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
        except ValidationError as e:
            raise ValueError(f"Validation failed: {e.errors()}")
        except Exception as e:
            raise ValueError(f"Message parsing failed: {e}")

    async def _send_error(self, error: Exception, context: Dict[str, Any]):
        """Отправка информации об ошибке в отдельный топик."""
        error_info = {
            "error_type": error.__class__.__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "context": context,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        logger.error(f"Processing error: {error_info['error_type']} - {error_info['error_message']}")

        try:
            await self.send_message(
                topic=self.error_topic,
                value=error_info,
                headers={
                    "error_type": error_info["error_type"],
                    "processor": self.processor_class.__name__,
                    "timestamp": error_info["timestamp"]
                }
            )
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")

    async def _send_result(self, task_data: Dict[str, Any], result: Any):
        """Отправка результата обработки."""
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

        logger.info(f"Task {task_data.get('task_id', 'unknown')} completed")

    async def _execute_processor(self, task_data: Dict[str, Any]) -> Any:
        """
        Выполнение обработки задачи с помощью загруженного процессора.

        Args:
            task_data: Валидированные данные задачи

        Returns:
            Результат обработки
        """
        # Создаем экземпляр процессора
        processor = self.processor_class()

        # Ищем метод обработки (process, execute, run, handle)
        process_method = None
        method_names = ["process", "execute", "run", "handle"]

        for method_name in method_names:
            method = getattr(processor, method_name, None)
            if method and callable(method):
                process_method = method
                break

        if not process_method:
            raise AttributeError(
                f"Processor {self.processor_class.__name__} must have one of: {', '.join(method_names)}"
            )

        # Вызываем метод обработки
        logger.debug(f"Executing {self.processor_class.__name__}.{process_method.__name__}")
        result = await process_method(**task_data)

        return result

    async def _process_single_task(self, task_data: Dict[str, Any]):
        """Обработка одной задачи воркером."""
        try:
            result = await self._execute_processor(task_data)
            await self._send_result(task_data, result)

        except Exception as e:
            logger.error(f"Task processing failed: {e}")
            await self._send_error(e, {"task_data": task_data})

    async def _worker_loop(self, worker_id: int):
        """
        Цикл обработки задач для одного воркера.

        Args:
            worker_id: Идентификатор воркера для логирования
        """
        logger.info(f"Worker {worker_id} started")

        while self._running:
            try:
                # Получаем задачу из очереди
                task_data = await self.task_queue.get()

                # None - сигнал остановки
                if task_data is None:
                    break

                # Обрабатываем задачу
                logger.debug(f"Worker {worker_id} processing task {task_data.get('task_id', 'unknown')}")
                await self._process_single_task(task_data)

            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
            finally:
                if task_data is not None:
                    self.task_queue.task_done()

        logger.info(f"Worker {worker_id} stopped")

    async def _process_incoming_message(self, msg: ConsumerRecord):
        """
        Обработка входящего сообщения: парсинг, валидация, добавление в очередь.

        Args:
            msg: Сообщение от Kafka
        """
        try:
            # Парсинг и валидация
            task_data = await self._parse_and_validate(msg)

            # Добавление в очередь задач
            await self.task_queue.put(task_data)

            # Подтверждение сообщения
            await self._consumer.commit()

            logger.debug(
                f"Message added to queue: "
                f"task_id={task_data.get('task_id', 'unknown')}, "
                f"queue_size={self.task_queue.qsize()}"
            )

        except Exception as e:
            logger.error(f"Failed to process incoming message: {e}")

            # Создаем контекст для ошибки
            error_context = {
                "original_message": msg.value.decode('utf-8') if msg.value else None,
                "message_metadata": {
                    "topic": msg.topic,
                    "partition": msg.partition,
                    "offset": msg.offset
                }
            }

            await self._send_error(e, error_context)

            # Пропускаем сообщение с ошибкой
            await self._consumer.commit()

    async def start(self):
        """
        Запуск сервиса с пулом воркеров.
        """
        if self._running:
            logger.warning("Service is already running")
            return

        self._running = True

        # Запуск продюсера и консьюмера
        await self.start_producer()
        await self.start_consumer(
            topic=self.consumer_topic,
            group_id=self.consumer_group,
            enable_auto_commit=False
        )

        # Запуск воркеров
        self.workers = [
            asyncio.create_task(self._worker_loop(i), name=f"worker-{i}")
            for i in range(self.max_workers)
        ]

        logger.info(f"Service started with {self.max_workers} workers")
        logger.info(f"Listening to: {self.consumer_topic}")
        logger.info(f"Sending results to: {self.producer_topic}")
        logger.info(f"Sending errors to: {self.error_topic}")

        try:
            # Главный цикл обработки входящих сообщений
            async for msg in self._consumer:
                if not self._running:
                    break

                logger.debug(
                    f"Received message: "
                    f"topic={msg.topic}, partition={msg.partition}, offset={msg.offset}"
                )

                await self._process_incoming_message(msg)

        except asyncio.CancelledError:
            logger.info("Service shutdown requested")
        except Exception as e:
            logger.critical(f"Error in main message loop: {e}")
            raise
        finally:
            await self.stop()

    async def stop(self):
        """
        Корректное завершение работы сервиса.
        """
        if not self._running:
            return

        self._running = False
        logger.info("Stopping service...")

        # Останавливаем воркеров
        logger.info(f"Stopping {len(self.workers)} workers...")
        for worker in self.workers:
            worker.cancel()

        # Ждем завершения воркеров
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)

        # Добавляем сигналы остановки в очередь
        for _ in range(self.max_workers):
            await self.task_queue.put(None)

        # Ждем завершения всех задач в очереди
        await self.task_queue.join()

        # Останавливаем Kafka клиенты
        await super().stop()

        logger.info("Service stopped successfully")


class ExampleRequestSchema(BaseModel):
    """
    Пример схемы для валидации входящих запросов.
    """
    task_id: str
    data: Dict[str, Any]
    priority: int = 1

    class Config:
        extra = "forbid"


class ExampleParallelProcessor:
    """
    Пример параллельного процессора.
    """

    async def process(self, task_id: str, data: Dict[str, Any], priority: int = 1) -> Dict[str, Any]:
        """
        Пример метода обработки.
        """
        logger.info(f"Processing task {task_id} with priority {priority}")

        # Имитация работы
        await asyncio.sleep(0.5)

        return {
            "task_id": task_id,
            "status": "processed",
            "result": f"Processed {len(data)} items",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


async def main():
    """
    Пример запуска сервиса.
    """
    import os

    config = {
        "processor_path": os.getenv("PROCESSOR_PATH", "example.parallel_processor"),
        "processor_class": os.getenv("PROCESSOR_CLASS", "ExampleParallelProcessor"),
        "validator_path": os.getenv("VALIDATOR_PATH", "example.schemas"),
        "consumer_group": os.getenv("CONSUMER_GROUP", "parallel-service-group"),
        "consumer_topic": os.getenv("CONSUMER_TOPIC", "parallel-requests"),
        "producer_topic": os.getenv("PRODUCER_TOPIC", "parallel-results"),
        "max_workers": int(os.getenv("MAX_WORKERS", "3")),
        "queue_size": int(os.getenv("QUEUE_SIZE", "10")),
        "kafka_servers": os.getenv("KAFKA_SERVERS", "localhost:9092"),
    }

    service = None
    try:
        service = ParallelProcessorService(
            processor_path=config["processor_path"],
            processor_class_name=config["processor_class"],
            validator_path=config["validator_path"],
            consumer_group=config["consumer_group"],
            consumer_topic=config["consumer_topic"],
            producer_topic=config["producer_topic"],
            max_workers=config["max_workers"],
            queue_size=config["queue_size"],
            bootstrap_servers=config["kafka_servers"]
        )

        logger.info("Starting parallel processor service...")
        await service.start()

    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
    except Exception as e:
        logger.critical(f"Service failed: {e}", exc_info=True)
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
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
