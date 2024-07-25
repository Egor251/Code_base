import aiogram
from aiogram import Router, F, html
import asyncio
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode
from aiogram import Bot, Dispatcher
import config

import inline_keyboard

# https://mastergroosha.github.io/aiogram-3-guide/messages/

# bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)  aiogram < 3.8
bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))  # aiogram > 3.8
router = Router()


@router.message(Command("button"))  # Рисуем inline кнопки
async def button_handler(msg: Message):

    await msg.answer(inline_keyboard.price_message, reply_markup=inline_keyboard.keyboard)  # Пишет ответ и добавляет кнопки

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
async def echo_with_format(message: Message):
    message_text = message.text  # Не сохраняет исходное форматирование
    message_html_text = message.html_text  # Сохраняет исходное форматирование
    # Создаём подчёркнутый текст
    added_text = html.underline(f"Подчёркнутый текст:")  # Сделает текст подчёркнутым
    # Отправляем новое сообщение с добавленным текстом
    await message.answer(f"{message.html_text}\n\n{added_text}", parse_mode="HTML")  # parse_mode=HTML обязательно, иначе не отображается подчёркнутый текст

@router.callback_query()
async def callback_query_handler(query: aiogram.types.CallbackQuery):

    await bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)  # Удаляем сообщение с кнопками так как больше не нужны


    await bot.answer_callback_query(query.id)  # Отвечаем обратно кнопке, что она была нажата

    await bot.send_invoice(
        chat_id=query.message.chat.id,  # id чата
        title='Товар 1',  # Название товара
        description=config.subscribe_description,  # Описание товара
        payload=str('Важная штука, её будем отлавливать далее'),  # Дополнительная информация
        provider_token=config.payment_token,  # Токен провайдера  https://core.telegram.org/bots/payments
        start_parameter="start_parameter",  # Надо выяснить...
        currency="rub",  # Валюта
        prices=[aiogram.types.LabeledPrice(
                label='Товар 1',  # Наименование товара
                amount='1000'  # Стоимость товара в копейках!
                )],
        max_tip_amount=5000,
        suggested_tip_amounts=[1000, 2000, 3000],
        request_timeout=15
    )

@router.pre_checkout_query(lambda query: True)  # Проверка на корректность оплаты
async def pre_checkout_handler(query: aiogram.types.PreCheckoutQuery):
    print('Чекаут')
    await bot.answer_pre_checkout_query(query.id, ok=True)  # ok=True позволяет оплатить с помощью кнопки


@router.message(F.successful_payment)  # функция выполнится после успешной оплаты  (F.successful_payment) Капец важно!
async def process_successful_payment(message: Message):

    user_id = message.chat.id  # получаем id пользователя для внесения в базу

    await bot.send_message(
        message.chat.id, f'Спасибо за покупку!')
