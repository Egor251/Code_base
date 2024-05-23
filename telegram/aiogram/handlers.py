import aiogram
from aiogram import Router, F, html
import asyncio
from aiogram.types import Message
from aiogram.filters import Command
import config

# https://mastergroosha.github.io/aiogram-3-guide/messages/

router = Router()


@router.message(Command("button"))  # Рисуем кнопки
async def button_handler(msg: Message):
    kb = [
        [aiogram.types.KeyboardButton(text="1")],
        [aiogram.types.KeyboardButton(text="1")]
    ]
    keyboard = aiogram.types.ReplyKeyboardMarkup(keyboard=kb)
    await msg.answer("Кнопки", reply_markup=keyboard)  # Пишет ответ и добавляет кнопки

@router.message(Command("start"))  # Обработка команды /start, отправленной боту
async def start_handler(msg: Message):
    await msg.answer("Hello world!")


    # Если бот должен выполнять вечный цикл, то лучше запускать его командой старт
    while True:
        await msg.answer(f'Infinite loop')  # msg.answer('text')  # отправит сообщение все пользоавателям кто вводил команду /start после запуска бота (ошибка?)
        #await msg.send_message(msg.from_user.id, 'текст')  # Должно отправить сообщение отправившему команду /start
        await asyncio.sleep(float(1000))  # Неблокирующая задержка бесконечного цикла


@router.message()  # Обработчик любого сообщения
async def message_handler(msg: Message):
    text = msg.text.split(' ')  # Разбиваем сообщение на слова и обрабатываем

    #await msg.answer(f"Wrong command! Try again.")
    #await msg.answer(f"Твой ID: {msg.from_user.id}")
    #await msg.answer(type(msg))

@router.message(F.text)
async def echo_with_time(message: Message):
    message_text = message.text  # Не сохраняет исходное форматирование
    message_html_text = message.html_text  # Сохраняет исходное форматирование
    # Создаём подчёркнутый текст
    added_text = html.underline(f"Подчёркнутый текст:")  # Сделает текст подчёркнутым
    # Отправляем новое сообщение с добавленным текстом
    await message.answer(f"{message.html_text}\n\n{added_text}", parse_mode="HTML")  # parse_mode=HTML обязательно, иначе не отображается подчёркнутый текст

@router.message(Command("buy"))
async def pay(message: Message, bot: aiogram.Bot):
    await bot.send_invoice(
        chat_id=message.chat.id,            # id чата
        title="Товар",                      # Название товара
        description="Описание товара",      # Описание товара
        payload="payload",                  # Дополнительная информация
        provider_token="provider_token",    # Токен провайдера  https://core.telegram.org/bots/payments
        start_parameter="start_parameter",  # Надо выяснить...
        currency="rub",                     # Валюта
        prices=[
            aiogram.types.LabeledPrice(
                label="Товар 1",
                amount=1000                 # Стоимость товара в копейках! То есть это 10 рублей
            ),
            aiogram.types.LabeledPrice(
                label="Товар 2",
                amount=2000                 # Стоимость товара в копейках! То есть это 20 рублей
            )
        ],
    max_tip_amount=5000,
    suggested_tip_amounts=[1000, 2000, 3000],
    request_timeout=15
    )