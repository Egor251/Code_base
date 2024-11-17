"""
Файл с Основным классом Kafka. Он будет наследоваться другими классами для передачи методов взаимодействия с kafka
"""
import settings
import json

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer


class KafkaClass:
    """
      Блок Kafka
      """

    @staticmethod
    async def start_consumer() -> AIOKafkaConsumer:  # Эта функция создаёт экземпляр консьюмера. Просто для удобства
        """
        Стартовый поток для получения данных из Kafka.
        :return: AIOKafkaConsumer
        """

        consumer = AIOKafkaConsumer(  # создаём подключение консьюмера, задаём топик и адрес кафки
            settings.CONSUME_TOPIC,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        )
        await consumer.start()
        print('Starting Kafka consumer')
        return consumer

    @staticmethod
    async def send_to_kafka(data: list[dict] or dict) -> None:
        """
        Отправляет данные в Kafka.
        :param data: Данные для отправки
        :return: None
        """

        producer = AIOKafkaProducer(  # создаём подключение продюсера
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        )

        # Этого кода достаточно для отправки сообщения data
        await producer.start()
        # Топик можно задавать не при подклюючении, а передавать отдельно
        await producer.send_and_wait(settings.PRODUCE_TOPIC, json.dumps(data).encode())
        await producer.stop()

    async def consume(self, func) -> None:
        """
        Получает данные из Kafka и отправляет их в Shodan.
        :return: None
        """

        consumer = await self.start_consumer()
        print('consumer started')
        try:
            async for msg in consumer:
                print(f'Received message: {msg.value.decode()}')  # через кафку шлём и получаем json

                result = {func(msg.value.decode())}  # Это не обязательно, но можно обработать полученное сообщение функцией func и отправить обратно

                await self.send_to_kafka(result)
        except Exception as e:
            print(f'Error: {e}')
        finally:
            await consumer.stop()
