from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


buttons = [[]]
price_message = 'Доступные подписки: \n\n'
goods = [['Подписка 1', '30']]  # В данном случае [надпись на кнопке, возвращаемое значение после нажатия]

for good in goods:

    price_message += f'{good[0]}\n'
    buttons[0].append(InlineKeyboardButton(text=good[0], callback_data=str(good[1])))


keyboard = InlineKeyboardMarkup(row_width=3, inline_keyboard=buttons)