import asyncio

# Код будет непрерывно получать данные из двух источников, а третья функция выполнится если хоть одна из функций получит данные
async def get_data_1():

    return "Data 1"

async def get_data_2():
    return 'Data 2'

async def process_data(data):
    print(data)


async def function_1(queue):
    while True:
        data = await get_data_1()  # заменить на реальный код получения данных
        await queue.put(data)  # отправляем данные в очередь
        await asyncio.sleep(2)


async def function_2(queue):
    while True:
        data = await get_data_2()  # заменить на реальный код получения данных
        await queue.put(data)  # отправляем данные в очередь
        await asyncio.sleep(5)


async def function_3(queue):
    while True:
        data = await queue.get()  # получаем данные из очереди
        await process_data(data)  # заменить на реальный код обработки данных

async def main():
    queue = asyncio.Queue()

    task1 = asyncio.create_task(function_1(queue))
    task2 = asyncio.create_task(function_2(queue))
    task3 = asyncio.create_task(function_3(queue))

    await asyncio.gather(task1, task2, task3)

asyncio.run(main())