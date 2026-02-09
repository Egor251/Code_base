"""
Файл с Основным классом Kafka. Он будет наследоваться другими классами для передачи методов взаимодействия с kafka
"""
import os
import json
from loguru import logger
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import asyncio
from dotenv import load_dotenv


load_dotenv()

logger.add('log.log', rotation="10 MB", retention="30 days", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

class KafkaBase:
    """
    Базовый класс для работы с Kafka
    """

    def __init__(self, loop=None):
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
        self._consumer = None
        self._producer = None

    async def start_producer(self):
        """Инициализация продюсера"""
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            loop=asyncio.get_running_loop(),
            acks='all'
        )
        await self._producer.start()

    async def start_consumer(self, topic: str, group_id: str = None, **kwargs):
        """Инициализация консьюмера"""
        self._consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=group_id,
            loop=asyncio.get_running_loop(),
            **kwargs
        )
        await self._consumer.start()
        return self._consumer

    async def send_message(self, topic: str, value: dict, key: str = None, headers: dict = None):
        """Отправка сообщения с обработкой ошибок"""
        try:
            await self.start_producer()

            headers = [(k, v.encode()) for k, v in (headers or {}).items()]
            await self._producer.send(
                topic=topic,
                value=json.dumps(value).encode(),
                key=key.encode() if key else None,
                headers=headers
            )
            await self._producer.stop()
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise

    async def stop(self):
        """Корректное завершение"""
        try:
            if self._producer:
                await self._producer.stop()
            if self._consumer:
                await self._consumer.stop()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")