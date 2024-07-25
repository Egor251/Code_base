import os
import sys

try:
    import inspect
    import asyncio
    import logging
    from aiogram import Bot, Dispatcher
    from aiogram.enums.parse_mode import ParseMode
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.client.bot import DefaultBotProperties
except ImportError:
    os.system('python3 -m pip install -r requirements.txt')
    import inspect
    import asyncio
    import logging
    from aiogram import Bot, Dispatcher
    from aiogram.enums.parse_mode import ParseMode
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.client.bot import DefaultBotProperties

import config
from handlers import router


def get_script_dir(follow_symlinks=True):
    if getattr(sys, 'frozen', False):  # py2exe, PyInstaller, cx_Freeze
        path = os.path.abspath(sys.executable)
    else:
        path = inspect.getabsfile(get_script_dir)
    if follow_symlinks:
        path = os.path.realpath(path)
    return os.path.dirname(path)


os.chdir(get_script_dir())


async def main():
    # bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)  aiogram < 3.8
    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))  # aiogram > 3.8
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())