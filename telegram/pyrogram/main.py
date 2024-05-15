import config
import asyncio

from pyrogram import Client, filters
from pyrogram.types import Message

api_hash = config.api_hash
api_id = config.api_id

# with Client(name="my_account", api_hash=api_hash, api_id=api_id) as app:
#     app.send_message("me", "Это я бот")


client = Client(name="my_account", api_hash=api_hash, api_id=api_id)

@client.on_message(filters.private)
async def echo(client_object, message: Message):
    client_object.send_message(message.chat.id, f"вы сказали: {message.text}")  # Ответ обратно пользователю
    user_id = message.from_user.id  # Получаем id пользователя, от которого пришло сообщение и потом сохраняем где-нибудь
    text = message.text.lower()  # Получаем текст сообщения
    text_array = text.split(' ')  # Разбиваем текст на массив слов

    while True:  # Если нужен беспонечный цикл - используем его тут
        await client.send_message(user_id, 'Text')  # Отправляем сообщение пользователю

        await asyncio.sleep(5)

client.run()


if __name__ == '__main__':
    client.run()