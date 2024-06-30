import asyncio
import time

async def first():
    print(1)
    await asyncio.sleep(5)

async def second():
    print(2)
    await asyncio.sleep(10)

def main():
    start = time.time()

    # без event loop не будет работать асинхронно
    ioloop = asyncio.get_event_loop()  # Подключаемся к event loop
    tasks = [ioloop.create_task(first()), ioloop.create_task(second())]  # Сюда вносим все функции что должны быть асинхронными
    wait_tasks = asyncio.wait(tasks)
    ioloop.run_until_complete(wait_tasks)  # Запускаем event loop
    ioloop.close()  # По окончании работы закрываем event loop

    end = time.time() - start
    print(end)


if __name__ == '__main__':
    main()