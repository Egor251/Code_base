"""
KAFKA SERVICE EXAMPLES - Универсальные примеры использования

Этот файл содержит готовые примеры для быстрого копирования и адаптации.
Все примеры универсальны и не содержат специфичной бизнес-логики.

Структура файла:
1. Импорты и настройки
2. Базовый последовательный сервис (GenericService)
3. Параллельный сервис с воркерами (ParallelProcessorService)
4. Различные варианты использования
5. Общие рекомендации и best practices
"""

import asyncio
import logging
from typing import Dict, Any

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# ПРИМЕР 1: Базовый последовательный сервис (GenericService)
# ============================================================================

async def basic_sequential_service():
    """
    Универсальный пример запуска последовательного сервиса.

    Особенности:
    - Обработка сообщений строго по одному
    - Гарантия порядка обработки
    - Простая конфигурация

    Подходит для:
    ✅ Транзакционных операций
    ✅ Логирования и аудита
    ✅ Задач с зависимым контекстом
    ❌ CPU-intensive задач
    ❌ Высоконагруженных систем
    """

    # Пример конфигурации
    config = {
        'processor_path': 'your_module.processor',
        'processor_class_name': 'YourProcessor',
        'validator_path': 'your_module.schemas',
        'consumer_group': 'your-service-group',
        'consumer_topic': 'your-requests',
        'producer_topic': 'your-results',
        'error_topic_suffix': '-errors',
        'kafka_servers': 'localhost:9092'
    }

    # Инициализация сервиса
    from kafka_generic_service import GenericService

    service = GenericService(
        processor_path=config['processor_path'],
        processor_class_name=config['processor_class_name'],
        validator_path=config['validator_path'],
        consumer_group=config['consumer_group'],
        consumer_topic=config['consumer_topic'],
        producer_topic=config['producer_topic'],
        error_topic_suffix=config['error_topic_suffix'],
        bootstrap_servers=config['kafka_servers']
    )

    try:
        await service.start()
    except KeyboardInterrupt:
        await service.stop()
    except Exception as e:
        logger.error(f"Service failed: {e}")
        await service.stop()


# ============================================================================
# ПРИМЕР 2: Параллельный сервис с воркерами (ParallelProcessorService)
# ============================================================================

async def parallel_worker_service():
    """
    Универсальный пример запуска параллельного сервиса.

    Особенности:
    - Пул воркеров для параллельной обработки
    - Настраиваемое количество воркеров и размер очереди
    - Сохраняет порядок в рамках партиции

    Подходит для:
    ✅ Обработки изображений/видео
    ✅ Преобразования данных
    ✅ Web scraping
    ✅ ML инференса
    ❌ Транзакций с гарантией порядка
    """

    # Пример конфигурации для CPU-intensive задач
    config = {
        'processor_path': 'processing.image_transformer',
        'processor_class_name': 'ImageProcessor',
        'validator_path': 'processing.schemas',
        'consumer_group': 'image-processing-group',
        'consumer_topic': 'image-requests',
        'producer_topic': 'image-results',
        'max_workers': 10,  # Количество параллельных воркеров
        'queue_size': 20,  # Размер буфера очереди
        'error_topic_suffix': '-errors',
        'kafka_servers': 'kafka1:9092,kafka2:9092,kafka3:9092'
    }

    # Инициализация сервиса
    from kafka_generic_service_with_miltiple_workers import ParallelProcessorService

    service = ParallelProcessorService(
        processor_path=config['processor_path'],
        processor_class_name=config['processor_class_name'],
        validator_path=config['validator_path'],
        consumer_group=config['consumer_group'],
        consumer_topic=config['consumer_topic'],
        producer_topic=config['producer_topic'],
        max_workers=config['max_workers'],
        queue_size=config['queue_size'],
        error_topic_suffix=config['error_topic_suffix'],
        bootstrap_servers=config['kafka_servers']
    )

    try:
        await service.start()
    except KeyboardInterrupt:
        await service.stop()
    except Exception as e:
        logger.error(f"Parallel service failed: {e}")
        await service.stop()


# ============================================================================
# ПРИМЕР 3: ETL пайплайн данных
# ============================================================================

async def etl_data_pipeline():
    """
    Пример ETL (Extract-Transform-Load) пайплайна.

    Архитектура:
    1. Сырые данные → Kafka топик 'raw-data-input'
    2. Трансформация → DataTransformer.process()
    3. Результат → 'processed-data-output'
    4. Ошибки → 'processed-data-output-errors'

    Используется ParallelProcessorService для параллельной обработки файлов.
    """

    from kafka_generic_service_with_miltiple_workers import ParallelProcessorService

    service = ParallelProcessorService(
        processor_path='etl.transformers',
        processor_class_name='DataTransformer',
        validator_path='etl.schemas',
        consumer_group='etl-pipeline-group',
        consumer_topic='raw-data-input',
        producer_topic='processed-data-output',
        max_workers=5,  # Параллельная обработка файлов
        queue_size=15,
        error_topic_suffix='-errors'
    )

    await service.start()


# ============================================================================
# ПРИМЕР 4: AI/ML инференс сервис
# ============================================================================

async def ai_ml_inference_service():
    """
    Сервис для распределенного ML инференса.

    Особенности:
    - Меньше воркеров (ML модели часто GPU-bound)
    - Сериализация больших тензоров
    - Валидация входных данных

    Пример сообщения для классификации:
    {
        "request_id": "classify-001",
        "model": "bert-text-classifier",
        "input": {"text": "Текст для классификации"},
        "parameters": {"return_probs": true}
    }
    """

    from kafka_generic_service_with_miltiple_workers import ParallelProcessorService

    service = ParallelProcessorService(
        processor_path='ml_models.inference',
        processor_class_name='ModelInference',
        validator_path='ml_models.schemas',
        consumer_group='ai-inference-group',
        consumer_topic='ai-inference-requests',
        producer_topic='ai-inference-results',
        max_workers=2,  # ML модели часто GPU-bound
        queue_size=5,
        error_topic_suffix='-errors',
        # Дополнительные настройки Kafka
        session_timeout_ms=30000,
        max_poll_interval_ms=300000  # ML инференс может быть долгим
    )

    try:
        await service.start()
    except KeyboardInterrupt:
        await service.stop()


# ============================================================================
# ПРИМЕР 5: Уведомления и алерты
# ============================================================================

async def notification_service():
    """
    Сервис отправки уведомлений.

    Использует GenericService для гарантированной доставки:
    1. Email уведомления
    2. SMS сообщения
    3. Push-уведомления
    4. Webhook вызовы

    Требует гарантий доставки и порядка обработки.
    """

    from kafka_generic_service import GenericService

    service = GenericService(
        processor_path='notifications.sender',
        processor_class_name='NotificationSender',
        validator_path='notifications.schemas',
        consumer_group='notification-service-group',
        consumer_topic='notification-requests',
        producer_topic='notification-results',
        error_topic_suffix='-failed',
        # Настройки для надежной доставки
        enable_idempotence=True,
        acks='all',
        retries=5
    )

    await service.start()


# ============================================================================
# ПРИМЕР 6: Обработка файлов и документов
# ============================================================================

async def file_processing_service():
    """
    Сервис для обработки файлов: PDF, DOCX, изображения и т.д.

    Параллельная обработка файлов с ограничением памяти.
    Каждый воркер обрабатывает один файл за раз.
    """

    from kafka_generic_service_with_miltiple_workers import ParallelProcessorService

    service = ParallelProcessorService(
        processor_path='file_processing.handler',
        processor_class_name='FileProcessor',
        validator_path='file_processing.schemas',
        consumer_group='file-processing-group',
        consumer_topic='file-processing-requests',
        producer_topic='file-processing-results',
        max_workers=3,  # Ограничение по памяти/диску
        queue_size=10,
        error_topic_suffix='-errors'
    )

    await service.start()


# ============================================================================
# ПРИМЕР 7: Агрегация и аналитика данных
# ============================================================================

async def data_aggregation_service():
    """
    Сервис для агрегации и аналитики данных в реальном времени.

    Примеры использования:
    - Агрегация метрик
    - Расчет статистики
    - Обновление дашбордов
    """

    from kafka_generic_service import GenericService  # Последовательный для корректных агрегаций

    service = GenericService(
        processor_path='analytics.aggregator',
        processor_class_name='DataAggregator',
        validator_path='analytics.schemas',
        consumer_group='analytics-aggregation-group',
        consumer_topic='metrics-input',
        producer_topic='aggregated-metrics',
        error_topic_suffix='-errors'
    )

    await service.start()


# ============================================================================
# КОНФИГУРАЦИЯ И ЗАПУСК
# ============================================================================

def get_config(service_type: str) -> Dict[str, Any]:
    """
    Возвращает конфигурацию для разных типов сервисов.

    Args:
        service_type: Тип сервиса ('sequential', 'parallel', 'etl', 'ml', 'notification', 'file', 'analytics')

    Returns:
        Конфигурационный словарь
    """
    configs = {
        'sequential': {
            'description': 'Базовый последовательный сервис',
            'processor_path': 'services.processor',
            'processor_class_name': 'BaseProcessor',
            'validator_path': 'services.schemas',
            'consumer_group': 'base-service-group',
            'consumer_topic': 'service-requests',
            'producer_topic': 'service-results',
            'max_workers': 1,  # Для sequential всегда 1
            'queue_size': 10
        },
        'parallel': {
            'description': 'Параллельный сервис с 5 воркерами',
            'processor_path': 'processing.worker',
            'processor_class_name': 'ParallelWorker',
            'validator_path': 'processing.schemas',
            'consumer_group': 'parallel-worker-group',
            'consumer_topic': 'worker-requests',
            'producer_topic': 'worker-results',
            'max_workers': 5,
            'queue_size': 15
        },
        'etl': {
            'description': 'ETL пайплайн',
            'processor_path': 'etl.transformer',
            'processor_class_name': 'ETLTransformer',
            'validator_path': 'etl.schemas',
            'consumer_group': 'etl-pipeline-group',
            'consumer_topic': 'raw-data',
            'producer_topic': 'processed-data',
            'max_workers': 3,
            'queue_size': 10
        },
        'ml': {
            'description': 'ML инференс',
            'processor_path': 'ml.inference',
            'processor_class_name': 'MLInference',
            'validator_path': 'ml.schemas',
            'consumer_group': 'ml-inference-group',
            'consumer_topic': 'inference-requests',
            'producer_topic': 'inference-results',
            'max_workers': 2,
            'queue_size': 5
        }
    }

    return configs.get(service_type, configs['sequential'])


async def run_example(service_type: str = 'sequential'):
    """
    Запуск примера по типу сервиса.

    Args:
        service_type: Тип сервиса для запуска
    """
    config = get_config(service_type)

    if service_type in ['sequential', 'notification', 'analytics']:
        # Используем GenericService для последовательной обработки
        from kafka_generic_service import GenericService
        service = GenericService(
            processor_path=config['processor_path'],
            processor_class_name=config['processor_class_name'],
            validator_path=config['validator_path'],
            consumer_group=config['consumer_group'],
            consumer_topic=config['consumer_topic'],
            producer_topic=config['producer_topic']
        )
    else:
        # Используем ParallelProcessorService для параллельной обработки
        from kafka_generic_service_with_miltiple_workers import ParallelProcessorService
        service = ParallelProcessorService(
            processor_path=config['processor_path'],
            processor_class_name=config['processor_class_name'],
            validator_path=config['validator_path'],
            consumer_group=config['consumer_group'],
            consumer_topic=config['consumer_topic'],
            producer_topic=config['producer_topic'],
            max_workers=config['max_workers'],
            queue_size=config['queue_size']
        )

    logger.info(f"Starting {service_type} service: {config['description']}")
    await service.start()


# ============================================================================
# ОБЩИЕ РЕКОМЕНДАЦИИ
# ============================================================================

"""
BEST PRACTICES ДЛЯ ИСПОЛЬЗОВАНИЯ:

1. ВЫБОР ТИПА СЕРВИСА:
   - GenericService: когда важен порядок, транзакции, логирование
   - ParallelProcessorService: для CPU/IO-intensive задач, которые можно распараллелить

2. НАСТРОЙКА ВОРКЕРОВ:
   - CPU-bound задачи: max_workers = количество ядер CPU
   - IO-bound задачи: max_workers может быть больше
   - GPU-bound (ML): max_workers = количество доступных GPU

3. РАЗМЕР ОЧЕРЕДИ:
   - queue_size = max_workers * 2 (рекомендация)
   - Большая очередь: буферизация при пиковых нагрузках
   - Маленькая очередь: backpressure на продюсера

4. ОБРАБОТКА ОШИБОК:
   - Всегда настраивайте error_topic_suffix
   - Логируйте полный traceback
   - Игнорируйте "битые" сообщения после нескольких попыток

5. KAFKA НАСТРОЙКИ:
   - enable_auto_commit=False для ручного контроля
   - session_timeout_ms и max_poll_interval_ms для долгих операций
   - acks='all' для гарантированной доставки

6. GRACEFUL SHUTDOWN:
   - Всегда обрабатывайте KeyboardInterrupt
   - Завершайте работу воркеров корректно
   - Коммитите оффсеты перед остановкой

ПРИМЕР КОНФИГУРАЦИОННОГО ФАЙЛА (.env или config.yaml):

KAFKA_SERVERS: kafka1:9092,kafka2:9092
CONSUMER_GROUP: my-service-group
CONSUMER_TOPIC: my-requests
PRODUCER_TOPIC: my-results
MAX_WORKERS: 5
QUEUE_SIZE: 10
ERROR_TOPIC_SUFFIX: -errors
LOG_LEVEL: INFO
"""

if __name__ == "__main__":
    """
    Пример запуска: python kafka_service_examples.py [service_type]

    Доступные типы сервисов:
    - sequential: Базовый последовательный
    - parallel: Параллельный с воркерами
    - etl: ETL пайплайн
    - ml: ML инференс
    - notification: Сервис уведомлений
    - file: Обработка файлов
    - analytics: Аналитика данных
    """
    import sys

    service_type = sys.argv[1] if len(sys.argv) > 1 else 'sequential'

    try:
        asyncio.run(run_example(service_type))
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        sys.exit(1)