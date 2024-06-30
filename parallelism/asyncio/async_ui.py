import asyncio


async def example_task():  # просто какая-то задача что-то возвращающая
    print('Hello')
    await asyncio.sleep(1)
    return 1


async def ui():  # Имитируем интерфейс пользователя
    while True:
        data = await loop.run_in_executor(None, input, "Enter command: ")  # Ожидаем ввод команды

        print(data)


async def main():  # Основная функция, обеспечивающая асинхронность
    asyncio.create_task(ui())  # Да да, тут warning, но так надо. Если добавить await, то не работает параллельно

    await loop_func()


async def loop_func():  # Функция работающая параллельно на фоне
    while True:
        res = await asyncio.gather(example_task())  # Получаем данные через api например
        await asyncio.sleep(5)  # Период обновления в секундах


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()