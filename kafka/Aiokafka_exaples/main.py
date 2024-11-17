"""
Основной код для взаимодействия через Kafka
"""
from Kafka_class import KafkaClass
import asyncio


class Example(KafkaClass):
    """
    Пример работы с Kafka
    """

    @staticmethod
    def some_function(data: dict) -> str:
        """
        Функция для обработки полученных данных
        :param data: данные полученные из Shodan
        :return: ответ
        """

        print(f"Received data: {data}")

        return f'Got data: {data}'

    async def main(self) -> None:
        """
        Запускаем бота для получения данных с Shodan.
        :return: None
        """
        while True:
            print("Starting")
            consuming = asyncio.create_task(self.consume(self.some_function))
            await asyncio.gather(consuming)
            print("Bot has successfully started consuming")
